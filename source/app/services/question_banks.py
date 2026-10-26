"""Bounded personal collections of references, independent of question ownership."""
from app.core.errors import require
from app.db.mongo import oid, now, transaction
from app.models.documents import QuestionBankDocument
from app.services.questions import QuestionService


class QuestionBankService:
    def __init__(self, db):
        self.db, self.questions = db, QuestionService(db)

    def owned(self, bank_id, user_id, session=None):
        bank = self.db.question_banks.find_one({'_id': oid(bank_id), 'ownerId': oid(user_id)}, session=session)
        require(bank is not None, '题库不存在', 'NOT_FOUND', 404)
        return bank

    def create(self, user_id, name, description=''):
        require(name.strip(), '题库名称不能为空')
        stamp = now()
        bank = QuestionBankDocument(ownerId=oid(user_id), name=name.strip(), description=description,
                                     createdAt=stamp, updatedAt=stamp).to_bson()
        self.db.question_banks.insert_one(bank.copy())
        return bank

    def list(self, user_id, offset=0, limit=20):
        query = {'ownerId': oid(user_id)}
        return {'items': list(self.db.question_banks.find(query).sort([('updatedAt', -1), ('_id', -1)]).skip(offset).limit(limit)),
                'total': self.db.question_banks.count_documents(query), 'offset': offset, 'limit': limit}

    def detail(self, bank_id, user_id):
        def operation(session):
            bank = self.owned(bank_id, user_id, session)
            rows = []
            for item in bank['items']:
                # Revoked items remain removable but their content is no longer returned.
                q = self.db.question_definitions.find_one({'_id': item['questionId'], '$or': [
                    {'ownerId': oid(user_id)}, {'sharedWith': oid(user_id)}], 'archived': False}, session=session)
                if not q:
                    rows.append({**item, 'available': False})
                    continue
                version = item.get('pinnedVersion', q['currentVersion'])
                rows.append({**item, 'available': True, 'resolvedVersion': version,
                             'content': self.questions.version(q['_id'], version, session)['content']})
            return {**bank, 'items': rows}
        return transaction(self.db, operation)

    def patch(self, bank_id, user_id, revision, name, description):
        require(name.strip(), '题库名称不能为空')
        return self._change(bank_id, user_id, revision, lambda b, s: {'name': name.strip(), 'description': description})

    def member(self, bank_id, user_id, revision, question_id, pinned=None, remove=False):
        def changes(bank, session):
            qid = oid(question_id)
            if remove:
                return {'items': [x for x in bank['items'] if x['questionId'] != qid]}
            q = self.questions.accessible(qid, user_id, session, lock=True, active=True)
            if pinned is not None:
                self.questions.version(q['_id'], pinned, session)
            # Upsert supports explicitly switching a member's pinned/latest version.
            items = [x for x in bank['items'] if x['questionId'] != qid]
            require(len(items) < 200, '题库最多包含 200 道题目')
            items.append({'questionId': qid, **({'pinnedVersion': pinned} if pinned is not None else {})})
            return {'items': items}
        return self._change(bank_id, user_id, revision, changes)

    def _change(self, bank_id, user_id, revision, changes):
        def operation(session):
            bank = self.owned(bank_id, user_id, session)
            require(bank['revision'] == revision, '题库已变化，请刷新', 'BANK_CONFLICT', 409)
            fields = changes(bank, session)
            result = self.db.question_banks.find_one_and_update({'_id': bank['_id'], 'revision': revision},
                {'$set': {**fields, 'updatedAt': now()}, '$inc': {'revision': 1}}, session=session, return_document=True)
            require(result is not None, '题库并发修改冲突', 'BANK_CONFLICT', 409)
            return result
        return transaction(self.db, operation)
