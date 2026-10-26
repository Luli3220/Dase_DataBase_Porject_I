from copy import deepcopy
from bson import ObjectId
from pymongo.errors import WriteError, DuplicateKeyError
import pytest
from app.db.mongo import initialize, now
from app.models.documents import VersionDocument
from app.models.domain import Question
from tests.fixtures import fixture_questions


def test_optional_source_round_trip():
    q = fixture_questions()[0]
    assert 'source' not in Question.model_validate(q).model_dump(exclude_none=True)
    q['source'] = {'questionId': str(ObjectId()), 'questionVersion': 2}
    v = VersionDocument(surveyId=ObjectId(), version=1, state='draft', revision=0,
        settings={'anonymous': True}, questions=[q], createdAt=now(), sealedAt=None).to_bson()
    assert isinstance(v['questions'][0]['source']['questionId'], ObjectId)
    assert VersionDocument.model_validate(v).to_bson() == v


def test_validator_indexes_and_nondestructive_initialize(db):
    assert len(db.list_collection_names()) == 7
    old = {'_id': ObjectId(), 'username': 'old_user', 'passwordHash': 'synthetic', 'schemaVersion': 1, 'createdAt': now()}
    db.users.insert_one(deepcopy(old))
    persisted = db.users.find_one({'_id': old['_id']})
    initialize(db); initialize(db)
    assert db.users.find_one({'_id': old['_id']}) == persisted
    assert any(i.get('unique') for i in db.question_versions.list_indexes() if 'questionId' in i['key'])
    bad = {'questionId': ObjectId(), 'version': 1, 'parentVersion': None, 'restoredFromVersion': None,
        'changeType': 'create', 'content': {'type': 'number', 'title': '年龄', 'required': True, 'options': [], 'validation': {}},
        'createdBy': old['_id'], 'createdAt': now(), 'schemaVersion': 1}
    db.question_versions.insert_one(deepcopy(bad))
    with pytest.raises(DuplicateKeyError): db.question_versions.insert_one(deepcopy(bad))
    bad['version'] = 2; bad['content']['routingRules'] = []
    with pytest.raises(WriteError): db.question_versions.insert_one(bad)
