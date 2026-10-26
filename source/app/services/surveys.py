import secrets
from copy import deepcopy
from bson import ObjectId
from app.core.errors import require, DomainError
from app.db.mongo import now, oid, transaction
from app.rules.engine import validate_question_config
from app.models.documents import SurveyDocument, VersionDocument, questions_to_bson
from app.services.questions import QuestionService


class SurveyService:
    def __init__(self, db): self.db = db

    def owned(self, survey_id, user_id, session=None):
        survey = self.db.surveys.find_one({"_id": oid(survey_id)}, session=session)
        require(survey is not None, "问卷不存在", "NOT_FOUND", 404)
        require(survey["ownerId"] == oid(user_id), "只能管理自己创建的问卷", "FORBIDDEN", 403)
        return survey

    def create(self, user_id, data):
        data = deepcopy(data)
        require(data["title"].strip(), "标题不能为空")
        sid, stamp = ObjectId(), now()
        survey = {"_id": sid, "ownerId": oid(user_id), "publicId": secrets.token_urlsafe(18),
            "title": data["title"].strip(), "description": data.get("description", ""), "status": "draft",
            "submissionPolicy": data.get("submissionPolicy", "latest_only"), "deadlineAt": data.get("deadlineAt"),
            "publishedVersion": None, "draftVersion": 1, "writeRevision": 0, "hasSubmissions": False,
            "createdAt": stamp, "updatedAt": stamp, "schemaVersion": 1}
        version = {"_id": ObjectId(), "surveyId": sid, "version": 1, "schemaVersion": 1, "state": "draft", "revision": 0,
            "settings": {"anonymous": data.get("anonymous", True)}, "questions": [], "createdAt": stamp, "sealedAt": None}
        survey = SurveyDocument.model_validate(survey).to_bson()
        version = VersionDocument.model_validate(version).to_bson()
        def operation(session):
            self.db.surveys.insert_one(survey.copy(), session=session)
            self.db.survey_versions.insert_one(version.copy(), session=session)
            return survey
        return transaction(self.db, operation)

    def draft(self, survey_id, user_id):
        survey = self.owned(survey_id, user_id)
        require(survey["draftVersion"] is not None, "没有草稿，请从发布版派生", "NO_DRAFT", 409)
        return self.db.survey_versions.find_one({"surveyId": survey["_id"], "version": survey["draftVersion"]})

    def edit(self, survey_id, user_id, data):
        return transaction(self.db, lambda session: self._edit(survey_id, user_id, data, session))

    def _edit(self, survey_id, user_id, data, session):
        # Empty draft is allowed to save; all non-empty configurations must be consistent.
        questions = validate_question_config(data["questions"], allow_empty=True)
        survey = self.owned(survey_id, user_id, session)
        old = self.db.survey_versions.find_one({'surveyId': survey['_id'], 'version': survey['draftVersion'],
            'state': 'draft', 'revision': data['expectedRevision']}, session=session)
        require(old is not None, '草稿已变更或冻结，请刷新', 'DRAFT_CONFLICT', 409)
        QuestionService(self.db).validate_sources(questions, old['questions'], user_id, session)
        result = self.db.survey_versions.find_one_and_update({'_id': old['_id'], 'state': 'draft', 'revision': data['expectedRevision']},
            {'$set': {'questions': questions_to_bson(questions), 'settings': data['settings']}, '$inc': {'revision': 1}}, return_document=True, session=session)
        require(result is not None, '草稿已变更或冻结，请刷新', 'DRAFT_CONFLICT', 409)
        return result

    def save(self, survey_id, user_id, changes, draft):
        # Share a single session: metadata, draft, and any source permission writes
        # either all commit or all roll back. Existing separate APIs stay available.
        def operation(session):
            survey = self._patch(survey_id, user_id, changes, session)
            version = self._edit(survey_id, user_id, draft, session)
            return {'survey': survey, 'draft': version}
        return transaction(self.db, operation)

    def import_question(self, survey_id, user_id, question_id, version, revision, replace_local_id=None):
        def operation(session):
            survey = self.owned(survey_id, user_id, session)
            draft = self.db.survey_versions.find_one({'surveyId': survey['_id'], 'version': survey['draftVersion'],
                'state': 'draft', 'revision': revision}, session=session)
            require(draft is not None, '草稿已变更或冻结，请刷新', 'DRAFT_CONFLICT', 409)
            library = QuestionService(self.db)
            q = library.accessible(question_id, user_id, session, lock=True, active=True)
            v = library.version(q['_id'], version, session)
            qs = deepcopy(draft['questions'])
            if replace_local_id:
                index = next((i for i, old in enumerate(qs) if old['id'] == replace_local_id), None)
                require(index is not None, '待替换题目不存在', 'NOT_FOUND', 404)
                # Keep incoming routing references stable; clear outgoing rules explicitly.
                local_id = replace_local_id
            else:
                require(len(qs) < 100, '问卷最多 100 题')
                index, local_id = len(qs), 'lib_' + ObjectId().__str__()
            instance = {'id': local_id, **v['content'], 'routingRules': [],
                        'source': {'questionId': str(q['_id']), 'questionVersion': version}}
            if index == len(qs): qs.append(instance)
            else: qs[index] = instance
            qs = validate_question_config(qs)
            library.validate_sources(qs, draft['questions'], user_id, session)
            result = self.db.survey_versions.find_one_and_update({'_id': draft['_id'], 'state': 'draft', 'revision': revision},
                {'$set': {'questions': questions_to_bson(qs)}, '$inc': {'revision': 1}}, session=session, return_document=True)
            require(result is not None, '草稿并发修改冲突', 'DRAFT_CONFLICT', 409)
            return result
        return transaction(self.db, operation)

    def derive(self, survey_id, user_id):
        def operation(session):
            s = self.owned(survey_id, user_id, session)
            require(s["publishedVersion"] is not None, "尚未发布", "NO_PUBLISHED_VERSION", 409)
            if s["draftVersion"] is not None:
                return self.db.survey_versions.find_one({"surveyId": s["_id"], "version": s["draftVersion"]}, session=session)
            # Survey update in this transaction serializes version allocation; no count()+1.
            v = self.db.survey_versions.find_one({"surveyId": s["_id"], "version": s["publishedVersion"]}, session=session)
            v = {**v, "_id": ObjectId(), "version": s["publishedVersion"] + 1, "state": "draft", "revision": 0, "sealedAt": None, "createdAt": now()}
            v = VersionDocument.model_validate(v).to_bson()
            self.db.surveys.update_one({"_id": s["_id"]}, {"$set": {"draftVersion": v["version"], "updatedAt": now()}, "$inc": {"writeRevision": 1}}, session=session)
            self.db.survey_versions.insert_one(v, session=session)
            return v
        return transaction(self.db, operation)

    def publish(self, survey_id, user_id, revision, after_seal=None):
        s = self.owned(survey_id, user_id)
        require(s["status"] != "closed", "已关闭问卷不能重新发布", "SURVEY_CLOSED", 409)
        if s["draftVersion"] is None:
            require(s["publishedVersion"] is not None, "无可发布版本", "NO_DRAFT", 409)
            v = self.db.survey_versions.find_one({"surveyId": s["_id"], "version": s["publishedVersion"]})
            require(v["revision"] == revision, "发布版本与预期不符", "DRAFT_CONFLICT", 409)
            return s  # Successful retry after a lost HTTP response.
        v = self.db.survey_versions.find_one({"surveyId": s["_id"], "version": s["draftVersion"]})
        require(v["revision"] == revision, "草稿版本冲突，请刷新", "DRAFT_CONFLICT", 409)
        validate_question_config(v["questions"])
        if v["state"] == "draft":
            result = self.db.survey_versions.update_one({"_id": v["_id"], "state": "draft", "revision": revision}, {"$set": {"state": "sealed", "sealedAt": now()}})
            require(result.modified_count == 1, "草稿已被修改，请刷新", "DRAFT_CONFLICT", 409)
        if after_seal: after_seal()  # Fault injection point: retry safely resumes sealed draft.
        result = self.db.surveys.find_one_and_update({"_id": s["_id"], "draftVersion": v["version"], "status": {"$ne": "closed"}},
            {"$set": {"publishedVersion": v["version"], "draftVersion": None, "status": "published", "updatedAt": now()}, "$inc": {"writeRevision": 1}}, return_document=True)
        if result is None:
            result = self.owned(survey_id, user_id)
            require(result["publishedVersion"] == v["version"] and result["status"] == "published", "发布指针切换失败；冻结草稿保留，可重试", "PUBLISH_CONFLICT", 409)
        return result

    def patch(self, survey_id, user_id, changes):
        return transaction(self.db, lambda session: self._patch(survey_id, user_id, changes, session))

    def _patch(self, survey_id, user_id, changes, session):
        changes = dict(changes)
        require(all(v is not None for k, v in changes.items() if k != "deadlineAt"), "字段不能为 null")
        if "title" in changes:
            require(changes["title"].strip(), "标题不能为空")
            changes["title"] = changes["title"].strip()
        s = self.owned(survey_id, user_id, session)
        if "submissionPolicy" in changes:
            require(not s["hasSubmissions"] or changes["submissionPolicy"] == s["submissionPolicy"], "首次提交后不能修改重复填写策略", "POLICY_LOCKED", 409)
        return self.db.surveys.find_one_and_update({"_id": s["_id"]}, {"$set": {**changes, "updatedAt": now()}, "$inc": {"writeRevision": 1}}, return_document=True, session=session)

    def close(self, survey_id, user_id):
        s = self.owned(survey_id, user_id)
        return self.db.surveys.find_one_and_update({"_id": s["_id"]}, {"$set": {"status": "closed", "updatedAt": now()}, "$inc": {"writeRevision": 1}}, return_document=True)

    def public(self, public_id, session=None):
        s = self.db.surveys.find_one({"publicId": public_id}, session=session)
        require(s is not None and s["publishedVersion"] is not None, "公开问卷不存在", "NOT_FOUND", 404)
        require(s["status"] == "published", "问卷已关闭", "SURVEY_CLOSED", 409)
        require(s["deadlineAt"] is None or now() < s["deadlineAt"], "问卷已截止", "SURVEY_EXPIRED", 409)
        v = self.db.survey_versions.find_one({"surveyId": s["_id"], "version": s["publishedVersion"], "state": "sealed"}, session=session)
        require(v is not None, "发布指针异常，请联系创建者", "PUBLISH_INCONSISTENT", 409)
        return s, v
