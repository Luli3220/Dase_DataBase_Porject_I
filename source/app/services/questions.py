"""Stable library identities and append-only versions; no survey-local routing here."""
import re
from bson import ObjectId
from app.core.errors import require
from app.db.mongo import now, oid, transaction
from app.models.domain import QuestionContent
from app.models.documents import QuestionDefinitionDocument, QuestionVersionDocument
from app.rules.engine import validate_question_config
from app.services.auth import normalize_username

CORE = ('type', 'title', 'required', 'options', 'validation')


def validated_content(content):
    content = QuestionContent.model_validate(content).model_dump()
    checked = validate_question_config([{'id': 'library', **content, 'routingRules': []}])[0]
    return {k: checked[k] for k in CORE}


class QuestionService:
    def __init__(self, db):
        self.db = db

    def accessible(self, question_id, user_id, session=None, owner=False, lock=False, active=False):
        uid = oid(user_id)
        q = self.db.question_definitions.find_one({'_id': oid(question_id)}, session=session)
        # A guessed private identity is indistinguishable from a missing identity.
        require(q is not None and (q['ownerId'] == uid or uid in q['sharedWith']), '题目不存在或未共享', 'NOT_FOUND', 404)
        require(not owner or q['ownerId'] == uid, '只有题目所有者可修改', 'FORBIDDEN', 403)
        require(not active or not q['archived'], '题目已归档，不能新引用', 'QUESTION_ARCHIVED', 409)
        if lock:
            # Serializes import/fork/member selection against sharing revocation/archive.
            self.db.question_definitions.update_one({'_id': q['_id']}, {'$inc': {'revision': 1}}, session=session)
        return q

    def version(self, question_id, version, session=None):
        require(type(version) is int and version >= 1, '版本号非法')
        v = self.db.question_versions.find_one({'questionId': oid(question_id), 'version': version}, session=session)
        require(v is not None, '题目版本不存在', 'NOT_FOUND', 404)
        return v

    def _create(self, user_id, content, session, forked_from=None):
        uid, stamp = oid(user_id), now()
        q = QuestionDefinitionDocument(ownerId=uid, currentVersion=1, forkedFrom=forked_from,
                                       createdAt=stamp, updatedAt=stamp).to_bson()
        v = QuestionVersionDocument(questionId=q['_id'], version=1, parentVersion=None, changeType='create',
            restoredFromVersion=None, content=content, createdBy=uid, createdAt=stamp).to_bson()
        self.db.question_definitions.insert_one(q.copy(), session=session)
        self.db.question_versions.insert_one(v.copy(), session=session)
        return {'definition': q, 'version': v}

    def create(self, user_id, content):
        content = validated_content(content)
        return transaction(self.db, lambda s: self._create(user_id, content, s))

    def detail(self, question_id, user_id):
        def operation(session):
            q = self.accessible(question_id, user_id, session)
            return self.dto(q, user_id, session)
        return transaction(self.db, operation)

    def dto(self, q, user_id, session=None):
        owner = self.db.users.find_one({'_id': q['ownerId']}, {'username': 1}, session=session)
        result = {k: q[k] for k in ('_id', 'ownerId', 'currentVersion', 'visibility', 'forkedFrom', 'archived', 'revision', 'createdAt', 'updatedAt')}
        result['ownerUsername'] = owner['username'] if owner else None
        result['canEdit'] = q['ownerId'] == oid(user_id)
        result['current'] = self.version(q['_id'], q['currentVersion'], session)
        if result['canEdit']:
            result['sharedUsernames'] = [u['username'] for u in self.db.users.find({'_id': {'$in': q['sharedWith']}}, {'username': 1}, session=session)]
        return result

    def list(self, user_id, search='', offset=0, limit=20, scope='accessible'):
        uid = oid(user_id)
        query = {'ownerId': uid} if scope == 'mine' else {'sharedWith': uid, 'ownerId': {'$ne': uid}} if scope == 'shared' else {'$or': [{'ownerId': uid}, {'sharedWith': uid}]}
        def operation(session):
            # Search version content in Mongo, before page selection; never regex interpolation.
            pipeline = [{'$match': query}, {'$lookup': {'from': 'question_versions', 'let': {'qid': '$_id', 'v': '$currentVersion'},
                'pipeline': [{'$match': {'$expr': {'$and': [{'$eq': ['$questionId', '$$qid']}, {'$eq': ['$version', '$$v']}]}}}], 'as': 'latest'}},
                {'$match': {'latest.content.title': {'$regex': re.escape(search), '$options': 'i'}}},
                {'$sort': {'updatedAt': -1, '_id': -1}}, {'$facet': {'items': [{'$skip': offset}, {'$limit': limit}], 'total': [{'$count': 'n'}]}}]
            rows = list(self.db.question_definitions.aggregate(pipeline, session=session))[0]
            return {'items': [self.dto(q, uid, session) for q in rows['items']], 'total': rows['total'][0]['n'] if rows['total'] else 0, 'offset': offset, 'limit': limit}
        return transaction(self.db, operation)

    def history(self, question_id, user_id, offset=0, limit=50):
        def operation(session):
            q = self.accessible(question_id, user_id, session)
            return {'items': list(self.db.question_versions.find({'questionId': q['_id']}, session=session).sort('version', -1).skip(offset).limit(limit)),
                    'total': q['currentVersion'], 'offset': offset, 'limit': limit}
        return transaction(self.db, operation)

    def append(self, question_id, user_id, expected, parent, content=None, restore=False):
        if content is not None:
            content = validated_content(content)
        def operation(session):
            q = self.accessible(question_id, user_id, session, owner=True, active=True)
            require(q['currentVersion'] == expected, '最新题目版本已变化，请刷新', 'VERSION_CONFLICT', 409)
            old = self.version(q['_id'], parent, session)
            version = expected + 1
            v = QuestionVersionDocument(questionId=q['_id'], version=version, parentVersion=parent,
                changeType='restore' if restore else 'update', restoredFromVersion=parent if restore else None,
                content=old['content'] if restore else content, createdBy=oid(user_id), createdAt=now()).to_bson()
            updated = self.db.question_definitions.update_one({'_id': q['_id'], 'currentVersion': expected},
                {'$set': {'currentVersion': version, 'updatedAt': now()}, '$inc': {'revision': 1}}, session=session)
            require(updated.modified_count == 1, '并发版本冲突', 'VERSION_CONFLICT', 409)
            self.db.question_versions.insert_one(v.copy(), session=session)
            return v
        return transaction(self.db, operation)

    def fork(self, question_id, user_id, version):
        def operation(session):
            q = self.accessible(question_id, user_id, session, lock=True, active=True)
            v = self.version(q['_id'], version, session)
            return self._create(user_id, v['content'], session, {'questionId': q['_id'], 'questionVersion': version})
        return transaction(self.db, operation)

    def sharing(self, question_id, user_id, usernames, revision):
        names = list(dict.fromkeys(normalize_username(n) for n in usernames))
        def operation(session):
            q = self.accessible(question_id, user_id, session, owner=True)
            users = list(self.db.users.find({'username': {'$in': names}}, {'_id': 1}, session=session))
            require(len(users) == len(names), '共享目标用户不存在')
            ids = [u['_id'] for u in users if u['_id'] != q['ownerId']]
            result = self.db.question_definitions.update_one({'_id': q['_id'], 'revision': revision},
                {'$set': {'sharedWith': ids, 'visibility': 'shared' if ids else 'private', 'updatedAt': now()}, '$inc': {'revision': 1}}, session=session)
            require(result.modified_count == 1, '题目已变化，请刷新', 'VERSION_CONFLICT', 409)
            return {'ok': True, 'revision': revision + 1}
        return transaction(self.db, operation)

    def archive(self, question_id, user_id, archived, revision):
        def operation(session):
            q = self.accessible(question_id, user_id, session, owner=True)
            result = self.db.question_definitions.update_one({'_id': q['_id'], 'revision': revision},
                {'$set': {'archived': archived, 'updatedAt': now()}, '$inc': {'revision': 1}}, session=session)
            require(result.modified_count == 1, '题目已变化，请刷新', 'VERSION_CONFLICT', 409)
            return {'ok': True, 'revision': revision + 1}
        return transaction(self.db, operation)

    def validate_sources(self, questions, previous, user_id, session):
        seen = set()
        prior = {q['id']: q for q in previous}
        for q in questions:
            source = q.get('source')
            if not source:
                continue
            qid, version = oid(source['questionId']), source['questionVersion']
            require(qid not in seen, '同一问卷版本不能重复引用同一全局题目')
            seen.add(qid)
            old = prior.get(q['id'], {})
            old_source = old.get('source')
            retained = old_source and oid(old_source['questionId']) == qid and old_source['questionVersion'] == version
            if not retained:
                self.accessible(qid, user_id, session, lock=True, active=True)
            frozen = self.version(qid, version, session)
            require({k: q[k] for k in CORE} == frozen['content'],
                    '关联题内容不能直接修改；请解除关联或导入新版本', 'SOURCE_MISMATCH', 409)
