from bson import ObjectId
import pytest
from app.db.mongo import now
from app.services.submissions import owner_submission


@pytest.mark.parametrize('anonymous,username', [(False, 'registered_reader'), (False, None), (True, 'must_stay_private')])
def test_owner_dto_identity_allowlist(anonymous, username):
    record = {'_id': ObjectId(), 'surveyVersion': 1, 'anonymousAtSubmission': anonymous,
              'respondentId': ObjectId(), 'respondentUsername': 'untrusted_internal_value',
              'answers': [], 'submittedAt': now(), 'requestId': 'internal', 'payloadDigest': 'internal'}
    result = owner_submission(record, username)
    base = {'id', 'surveyVersion', 'anonymous', 'answers', 'submittedAt'}
    assert set(result) == (base if anonymous else base | {'respondentId', 'respondentUsername'})
    if anonymous:
        assert str(record['respondentId']) not in str(result)
        assert username not in str(result)
    else:
        assert result['respondentId'] == str(record['respondentId'])
        assert result['respondentUsername'] == username
