"""Mongo-only persistence. Multi-document writes require a replica set."""
from datetime import datetime, timezone
from bson import ObjectId
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
from app.core.errors import DomainError


def now():
    return datetime.now(timezone.utc)


def oid(value):
    if isinstance(value, ObjectId): return value
    try: return ObjectId(value)
    except Exception: raise DomainError("NOT_FOUND", "资源不存在", 404)


def client_for(uri):
    return MongoClient(uri, tz_aware=True, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)


def transaction(db, callback):
    with db.client.start_session() as session:
        return session.with_transaction(callback, read_concern=ReadConcern("snapshot"), write_concern=WriteConcern("majority"), max_commit_time_ms=5000)


def schema(properties, required):
    return {"$jsonSchema": {"bsonType": "object", "required": ["_id", "schemaVersion", *required],
                            "properties": {"_id": {"bsonType": "objectId"}, "schemaVersion": {"enum": [1]}, **properties}}}


ID = {"bsonType": "objectId"}
DATE = {"bsonType": "date"}
INT = {"bsonType": "int", "minimum": 1}
NULLINT = {"bsonType": ["int", "null"], "minimum": 1}
STR = {"bsonType": "string"}
BOOL = {"bsonType": "bool"}
SCHEMAS = {
    "users": schema({"username": {"bsonType": "string", "minLength": 3, "maxLength": 40}, "passwordHash": STR, "createdAt": DATE, "sessionVersion": INT}, ["username", "passwordHash", "createdAt"]),
    "surveys": schema({"ownerId": ID, "publicId": STR, "title": STR, "description": STR,
        "status": {"enum": ["draft", "published", "closed"]}, "submissionPolicy": {"enum": ["latest_only", "multiple"]},
        "publishedVersion": NULLINT, "draftVersion": NULLINT, "deadlineAt": {"bsonType": ["date", "null"]},
        "createdAt": DATE, "updatedAt": DATE, "writeRevision": {"bsonType": "int"}, "hasSubmissions": BOOL},
        ["ownerId", "publicId", "title", "description", "status", "submissionPolicy", "publishedVersion", "draftVersion", "deadlineAt", "createdAt", "updatedAt", "writeRevision", "hasSubmissions"]),
    "survey_versions": schema({"surveyId": ID, "version": INT, "state": {"enum": ["draft", "sealed"]},
        "revision": {"bsonType": "int", "minimum": 0}, "settings": {"bsonType": "object", "required": ["anonymous"], "properties": {"anonymous": BOOL}},
        "questions": {"bsonType": "array", "maxItems": 100, "items": {"bsonType": "object", "required": ["id", "type", "title", "required", "options", "validation", "routingRules"],
            "properties": {"id": STR, "type": {"enum": ["single_choice", "multiple_choice", "text", "number"]}, "title": STR, "required": BOOL,
                "options": {"bsonType": "array", "maxItems": 50}, "validation": {"bsonType": "object"}, "routingRules": {"bsonType": "array", "maxItems": 20}}}},
        "createdAt": DATE, "sealedAt": {"bsonType": ["date", "null"]}}, ["surveyId", "version", "state", "revision", "settings", "questions", "createdAt", "sealedAt"]),
    "submissions": schema({"surveyId": ID, "surveyVersion": INT, "respondentId": ID, "anonymousAtSubmission": BOOL,
        "requestId": STR, "payloadDigest": STR, "submittedAt": DATE,
        "answers": {"bsonType": "array", "maxItems": 100, "items": {"bsonType": "object", "required": ["questionId", "value"],
            "properties": {"questionId": STR, "value": {"bsonType": ["string", "array", "int", "long", "double"]}}}}},
        ["surveyId", "surveyVersion", "respondentId", "anonymousAtSubmission", "requestId", "payloadDigest", "submittedAt", "answers"]),
}


def initialize(db):
    # Never drop or delete data. collMod is deliberately strict for future writes.
    for name, validator in SCHEMAS.items():
        if name not in db.list_collection_names():
            db.create_collection(name, validator=validator, validationLevel="strict", validationAction="error")
        else:
            db.command("collMod", name, validator=validator, validationLevel="strict", validationAction="error")
    db.users.create_index("username", unique=True)
    db.surveys.create_index("publicId", unique=True)
    db.surveys.create_index([("ownerId", ASCENDING), ("createdAt", DESCENDING)])
    db.survey_versions.create_index([("surveyId", ASCENDING), ("version", ASCENDING)], unique=True)
    db.submissions.create_index([("surveyId", ASCENDING), ("respondentId", ASCENDING), ("requestId", ASCENDING)], unique=True)
    db.submissions.create_index([("surveyId", ASCENDING), ("submittedAt", DESCENDING), ("_id", DESCENDING)])
    db.submissions.create_index([("surveyId", ASCENDING), ("surveyVersion", ASCENDING), ("submittedAt", DESCENDING)])
    db.submissions.create_index([("respondentId", ASCENDING), ("submittedAt", DESCENDING)])
