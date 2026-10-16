import hashlib
import json
from uuid import UUID
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from app.core.errors import require
from app.db.mongo import now, oid, transaction
from app.rules.engine import trace_path_and_validate_submission
from app.services.surveys import SurveyService
from app.models.documents import SubmissionDocument


def owner_submission(record, respondent_username=None):
    # Allowlist DTO: no requestId, digest, nested internal metadata or account map.
    result = {"id": str(record["_id"]), "surveyVersion": record["surveyVersion"], "anonymous": record["anonymousAtSubmission"],
              "answers": record["answers"], "submittedAt": record["submittedAt"]}
    if not record["anonymousAtSubmission"]:
        result["respondentId"] = str(record["respondentId"])
        result["respondentUsername"] = respondent_username
    return result


class SubmissionService:
    def __init__(self, db):
        self.db, self.surveys = db, SurveyService(db)

    def submit(self, public_id, user_id, data):
        try: require(str(UUID(data["requestId"])) == data["requestId"].lower(), "requestId 须为 UUID")
        except (ValueError, TypeError): require(False, "requestId 须为 UUID")
        # Digest exact logical JSON (answer array order ignored); whitespace differences conflict intentionally.
        try:
            payload = json.dumps({"surveyVersion": data["surveyVersion"], "answers": sorted(data["answers"], key=lambda a: a["questionId"])}, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(",", ":"))
        except (ValueError, TypeError): require(False, "答案必须是合法 JSON")
        digest = hashlib.sha256(payload.encode()).hexdigest()
        uid, request_id = oid(user_id), data["requestId"].lower()
        def operation(session):
            s = self.db.surveys.find_one({"publicId": public_id}, session=session)
            require(s is not None, "问卷不存在", "NOT_FOUND", 404)
            key = {"surveyId": s["_id"], "respondentId": uid, "requestId": request_id}
            old = self.db.submissions.find_one(key, session=session)
            if old:
                require(old["payloadDigest"] == digest, "相同 requestId 不能用于不同内容", "IDEMPOTENCY_CONFLICT", 409)
                return {"id": str(old["_id"]), "replayed": True, "surveyVersion": old["surveyVersion"]}
            s, v = self.surveys.public(public_id, session)
            require(data["surveyVersion"] == s["publishedVersion"], "问卷已更新，需要刷新重填", "SURVEY_VERSION_CHANGED", 409)
            answers, _ = trace_path_and_validate_submission(v["questions"], data["answers"])
            # Shared survey write forces serialization against policy/close/publish changes.
            self.db.surveys.update_one({"_id": s["_id"]}, {"$set": {"hasSubmissions": True}, "$inc": {"writeRevision": 1}}, session=session)
            record = {"_id": ObjectId(), **key, "surveyVersion": v["version"], "anonymousAtSubmission": v["settings"]["anonymous"],
                      "answers": answers, "payloadDigest": digest, "submittedAt": now(), "schemaVersion": 1}
            record = SubmissionDocument.model_validate(record).to_bson()
            self.db.submissions.insert_one(record, session=session)
            return {"id": str(record["_id"]), "replayed": False, "surveyVersion": record["surveyVersion"]}
        # A unique-key race may surface outside with_transaction's transient retry.
        try: return transaction(self.db, operation)
        except DuplicateKeyError: return transaction(self.db, operation)

    def selected(self, survey, version, mode, session=None):
        require(mode in ("current_effective", "historical_raw"), "统计口径非法")
        require(type(version) is int and version >= 1, "请指定已发布版本")
        v = self.db.survey_versions.find_one({"surveyId": survey["_id"], "version": version, "state": "sealed"}, session=session)
        require(v is not None and version <= (survey["publishedVersion"] or 0), "版本未发布或不存在", "NOT_FOUND", 404)
        pipeline = [{"$match": {"surveyId": survey["_id"]}}]
        if mode == "current_effective" and survey["submissionPolicy"] == "latest_only":
            pipeline += [{"$sort": {"submittedAt": -1, "_id": -1}}, {"$group": {"_id": "$respondentId", "record": {"$first": "$$ROOT"}}}, {"$replaceRoot": {"newRoot": "$record"}}]
        pipeline += [{"$match": {"surveyVersion": version}}, {"$sort": {"submittedAt": -1, "_id": -1}}]
        return v, pipeline

    def list_owner(self, survey_id, user_id, version=None, mode="historical_raw", offset=0, limit=50):
        def operation(session):
            s = self.surveys.owned(survey_id, user_id, session)
            selected_version = version if version is not None else s["publishedVersion"]
            _, pipeline = self.selected(s, selected_version, mode, session)
            result = list(self.db.submissions.aggregate(pipeline + [{"$facet": {"rows": [{"$skip": offset}, {"$limit": limit}], "total": [{"$count": "n"}]}}], session=session))[0]
            # Resolve only this page's non-anonymous identities, once, in the same snapshot.
            respondent_ids = {x["respondentId"] for x in result["rows"] if not x["anonymousAtSubmission"]}
            usernames = {u["_id"]: u["username"] for u in self.db.users.find(
                {"_id": {"$in": list(respondent_ids)}}, {"_id": 1, "username": 1}, session=session
            )} if respondent_ids else {}
            return {"version": selected_version, "mode": mode, "total": result["total"][0]["n"] if result["total"] else 0,
                    "offset": offset, "limit": limit, "items": [owner_submission(x, usernames.get(x["respondentId"])) for x in result["rows"]]}
        return transaction(self.db, operation)
