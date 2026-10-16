from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import pytest
from bson import ObjectId
from pymongo.errors import WriteError, DuplicateKeyError
from app.db.mongo import initialize, now
from app.core.errors import DomainError
from app.services.surveys import SurveyService
from app.services.submissions import SubmissionService
from app.services.statistics import StatisticsService
from tests.fixtures import fixture_questions, answers

pytestmark = pytest.mark.integration


def published(db, policy="latest_only"):
    owner = ObjectId()
    svc = SurveyService(db)
    s = svc.create(owner, {"title": "测试问卷", "anonymous": True, "submissionPolicy": policy})
    svc.edit(s["_id"], owner, {"expectedRevision": 0, "questions": fixture_questions(), "settings": {"anonymous": True}})
    return svc.publish(s["_id"], owner, 1), owner


def payload(**values): return {"surveyVersion": 1, "requestId": str(uuid4()), "answers": answers(**(values or {"q1": "no", "q3": 8}))}


def test_schema_indexes_bson(db):
    initialize(db); initialize(db)
    u = {"_id": ObjectId(), "username": "test", "passwordHash": "argon2", "createdAt": now(), "schemaVersion": 1}
    db.users.insert_one(u)
    with pytest.raises(DuplicateKeyError): db.users.insert_one({**u, "_id": ObjectId()})
    with pytest.raises(WriteError): db.users.insert_one({"username": "invalid"})
    s, owner = published(db)
    v = db.survey_versions.find_one({"surveyId": s["_id"]})
    assert isinstance(v["surveyId"], ObjectId) and v["createdAt"].tzinfo is not None
    assert v["questions"][1]["routingRules"][0]["condition"]["operand"] == ["python", "java"]
    with pytest.raises(DuplicateKeyError): db.surveys.insert_one({**s, "_id": ObjectId()})
    with pytest.raises(DuplicateKeyError): db.survey_versions.insert_one({**v, "_id": ObjectId()})


def test_version_cas_and_recovery(db):
    svc, owner = SurveyService(db), ObjectId()
    s = svc.create(owner, {"title": "recover"})
    with pytest.raises(DomainError): svc.publish(s["_id"], owner, 0)
    svc.edit(s["_id"], owner, {"expectedRevision": 0, "questions": fixture_questions(), "settings": {"anonymous": True}})
    with pytest.raises(DomainError): svc.edit(s["_id"], owner, {"expectedRevision": 0, "questions": fixture_questions(), "settings": {"anonymous": False}})
    def crash(): raise RuntimeError("simulated interruption")
    with pytest.raises(RuntimeError): svc.publish(s["_id"], owner, 1, after_seal=crash)
    assert db.surveys.find_one({"_id": s["_id"]})["publishedVersion"] is None
    with pytest.raises(DomainError): svc.public(s["publicId"])
    with pytest.raises(DomainError): svc.edit(s["_id"], owner, {"expectedRevision": 1, "questions": [], "settings": {"anonymous": False}})
    assert svc.publish(s["_id"], owner, 1)["publishedVersion"] == 1
    assert svc.publish(s["_id"], owner, 1)["publishedVersion"] == 1
    with ThreadPoolExecutor(4) as pool:
        versions = list(pool.map(lambda _: svc.derive(s["_id"], owner), range(4)))
    assert {v["version"] for v in versions} == {2}
    assert db.survey_versions.count_documents({"surveyId": s["_id"]}) == 2
    assert svc.public(s["publicId"])[1]["version"] == 1


def test_idempotency_stats_versions_privacy(db):
    s, owner = published(db); uid = ObjectId()
    subs, stats, svc = SubmissionService(db), StatisticsService(db), SurveyService(db)
    p = payload(); first = subs.submit(s["publicId"], uid, p)
    assert subs.submit(s["publicId"], uid, p)["id"] == first["id"]
    changed = {**p, "answers": answers(q1="no", q3=9)}
    with pytest.raises(DomainError): subs.submit(s["publicId"], uid, changed)
    subs.submit(s["publicId"], uid, payload(q1="yes", q2=["python", "java"], q4="  中文  "))
    st = stats.statistics(s["_id"], owner)
    assert (st["rawSubmissionCount"], st["effectiveSubmissionCount"]) == (2, 1)
    assert st["questions"][2]["mean"] is None
    assert st["questions"][1]["answeredCount"] == 1
    assert sum(o["count"] for o in st["questions"][1]["options"]) == 2
    raw = stats.statistics(s["_id"], owner, mode="historical_raw")
    assert raw["questions"][2]["mean"] == 8
    listing = subs.list_owner(s["_id"], owner)
    assert "respondentId" not in str(listing) and str(uid) not in str(listing)
    assert "requestId" not in str(listing)
    with pytest.raises(DomainError): svc.patch(s["_id"], owner, {"submissionPolicy": "multiple"})
    svc.derive(s["_id"], owner)
    svc.edit(s["_id"], owner, {"expectedRevision": 0, "questions": fixture_questions(), "settings": {"anonymous": False}})
    svc.publish(s["_id"], owner, 1)
    p2 = {**payload(), "surveyVersion": 2}
    subs.submit(s["publicId"], uid, p2)
    assert stats.statistics(s["_id"], owner, 1)["effectiveSubmissionCount"] == 0
    assert stats.statistics(s["_id"], owner, 1, "historical_raw")["rawSubmissionCount"] == 2
    assert "respondentId" not in str(subs.list_owner(s["_id"], owner, 1))
    assert subs.list_owner(s["_id"], owner, 2)["items"][0]["respondentId"] == str(uid)
    with pytest.raises(DomainError) as error: subs.submit(s["publicId"], uid, payload())
    assert error.value.code == "SURVEY_VERSION_CHANGED"


def test_multiple_concurrency_and_deadlines(db):
    s, owner = published(db, "multiple"); subs, svc = SubmissionService(db), SurveyService(db)
    uid, p = ObjectId(), payload()
    with ThreadPoolExecutor(6) as pool:
        ids = list(pool.map(lambda _: subs.submit(s["publicId"], uid, p)["id"], range(6)))
    assert len(set(ids)) == 1
    with ThreadPoolExecutor(4) as pool:
        list(pool.map(lambda _: subs.submit(s["publicId"], ObjectId(), payload()), range(4)))
    assert StatisticsService(db).statistics(s["_id"], owner)["effectiveSubmissionCount"] == 5
    duplicate = db.submissions.find_one({})
    with pytest.raises(DuplicateKeyError): db.submissions.insert_one({**duplicate, "_id": ObjectId()})
    svc.patch(s["_id"], owner, {"deadlineAt": now()})
    with pytest.raises(DomainError) as e: subs.submit(s["publicId"], uid, payload())
    assert e.value.code == "SURVEY_EXPIRED"
    svc.close(s["_id"], owner)
    with pytest.raises(DomainError) as e: subs.submit(s["publicId"], uid, payload())
    assert e.value.code == "SURVEY_CLOSED"
