import os
from bson import ObjectId
from pymongo import MongoClient
from pymongo.monitoring import CommandListener
import pytest
from app.services.submissions import SubmissionService
from tests.fixtures import fixture_questions
from tests.integration.test_api import clients, register, make, submit

pytestmark = pytest.mark.integration


def assert_identity(row, user, anonymous):
    assert row['anonymous'] is anonymous
    if anonymous:
        assert 'respondentId' not in row and 'respondentUsername' not in row
        assert user['id'] not in str(row) and user['username'] not in str(row)
    else:
        assert row['respondentId'] == user['id']
        assert row['respondentUsername'] == user['username']


@pytest.mark.parametrize('anonymous', [True, False])
@pytest.mark.parametrize('mode', ['historical_raw', 'current_effective'])
def test_api_owner_username_and_anonymity(clients, db, anonymous, mode):
    a, b, _ = clients
    register(a, 'owner'); reader = register(b, 'Reader_Actual')
    survey = make(a, anonymous=anonymous)
    response = submit(b, survey)
    assert response.status_code == 201
    stored = db.submissions.find_one({'_id': ObjectId(response.json()['id'])})
    assert stored['respondentId'] == ObjectId(reader['id'])
    assert 'respondentUsername' not in stored  # Read-time enrichment, not duplicated schema data.
    result = a.get(f"/api/surveys/{survey['_id']}/submissions?mode={mode}")
    assert result.status_code == 200
    assert result.json()['total'] == 1
    assert_identity(result.json()['items'][0], reader, anonymous)


@pytest.mark.parametrize('initial_anonymous', [True, False])
def test_api_identity_follows_submission_snapshot_across_versions(clients, initial_anonymous):
    a, b, _ = clients
    register(a, 'owner'); reader = register(b, 'history_reader')
    survey = make(a, anonymous=initial_anonymous)
    base = f"/api/surveys/{survey['_id']}"
    assert submit(b, survey).status_code == 201
    assert a.post(base + '/draft-from-published').status_code == 200
    assert a.put(base + '/draft', json={'expectedRevision': 0, 'settings': {'anonymous': not initial_anonymous},
                                      'questions': fixture_questions()}).status_code == 200
    assert a.post(base + '/publish', json={'expectedRevision': 1}).status_code == 200
    # Publishing a new setting alone must not alter the old effective record's privacy.
    assert_identity(a.get(base + '/submissions?version=1&mode=current_effective').json()['items'][0], reader, initial_anonymous)
    assert submit(b, survey, version=2).status_code == 201
    old = a.get(base + '/submissions?version=1&mode=historical_raw').json()
    assert_identity(old['items'][0], reader, initial_anonymous)
    assert a.get(base + '/submissions?version=1&mode=current_effective').json()['total'] == 0
    for mode in ('historical_raw', 'current_effective'):
        new = a.get(base + f'/submissions?version=2&mode={mode}').json()
        assert_identity(new['items'][0], reader, not initial_anonymous)
    # Statistics remain identity-free and keep the same version/deduplication semantics.
    stats = a.get(base + '/statistics?version=1&mode=historical_raw').json()
    assert stats['rawSubmissionCount'] == 1 and stats['effectiveSubmissionCount'] == 0
    assert 'respondentId' not in str(stats) and 'respondentUsername' not in str(stats)


class UserLookupCommands(CommandListener):
    def __init__(self): self.finds, self.aggregates = [], []

    def started(self, event):
        if event.command_name == 'find' and event.command.get('find') == 'users':
            self.finds.append(dict(event.command))
        if event.command_name == 'aggregate' and event.command.get('aggregate') == 'submissions':
            self.aggregates.append(dict(event.command))

    def succeeded(self, event): pass
    def failed(self, event): pass


def test_service_batches_only_current_page_non_anonymous_users(clients, db):
    a, b, _ = clients
    owner = register(a, 'owner')
    survey = make(a, anonymous=False, policy='multiple')
    users = []
    for i, count in enumerate((2, 2, 1)):
        users.append(register(b, f'page_reader_{i}'))
        for _ in range(count): assert submit(b, survey).status_code == 201
    listener = UserLookupCommands()
    with MongoClient(os.getenv('TEST_MONGO_URI', 'mongodb://127.0.0.1:27018/?replicaSet=rs0'),
                     tz_aware=True, event_listeners=[listener]) as client:
        service = SubmissionService(client[db.name])
        page = service.list_owner(survey['_id'], owner['id'], offset=1, limit=3)
        assert page['total'] == 5 and len(page['items']) == 3
        by_id = {u['id']: u for u in users}
        for row in page['items']: assert_identity(row, by_id[row['respondentId']], False)
        assert len(listener.finds) == 1  # One real Mongo command, not one per answer/user.
        lookup = listener.finds[0]
        expected_ids = {ObjectId(row['respondentId']) for row in page['items']}
        assert set(lookup['filter']['_id']['$in']) == expected_ids
        assert ObjectId(users[2]['id']) not in expected_ids  # Off-page users are not queried.
        assert lookup['projection'] == {'_id': 1, 'username': 1}
        assert lookup['lsid'] == listener.aggregates[0]['lsid']
        assert lookup['txnNumber'] == listener.aggregates[0]['txnNumber']
        listener.finds.clear()
        assert service.list_owner(survey['_id'], owner['id'], offset=99)['items'] == []
        assert listener.finds == []
        anonymous = make(a, anonymous=True)
        assert submit(b, anonymous).status_code == 201
        hidden = service.list_owner(anonymous['_id'], owner['id'])
        assert_identity(hidden['items'][0], users[2], True)
        assert listener.finds == []  # Anonymous-only pages do not resolve any accounts.


def test_api_missing_user_keeps_non_anonymous_id_and_returns_null_username(clients, db):
    a, b, _ = clients
    register(a, 'owner'); reader = register(b, 'removed_reader')
    survey = make(a, anonymous=False)
    assert submit(b, survey).status_code == 201
    db.users.delete_one({'_id': ObjectId(reader['id'])})  # This test's isolated database only.
    response = a.get(f"/api/surveys/{survey['_id']}/submissions")
    assert response.status_code == 200
    row = response.json()['items'][0]
    assert row['respondentId'] == reader['id'] and row['respondentUsername'] is None
