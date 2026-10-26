"""Small follow-up fixes: atomic editor save, active pagination and surveyCount."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from bson import ObjectId
import pytest
from app.core.errors import DomainError
from app.db.mongo import now
from app.services.surveys import SurveyService
from tests.integration.test_api import clients, register
from tests.project2.test_library import create_question, content, share
from tests.project2.test_import import survey, imported, publish
from tests.project2.test_statistics import answer, stat


def save(client, s, draft, metadata=None, **overrides):
    payload = {'expectedRevision': draft['revision'], 'settings': draft['settings'], 'questions': draft['questions']}
    payload.update(overrides)
    return client.post(f"/api/surveys/{s['_id']}/save", json={'metadata': metadata or {'title': '新标题'}, 'draft': payload})


def documents(db, s):
    sid = ObjectId(s['_id'])
    return (db.surveys.find_one({'_id': sid}), list(db.survey_versions.find({'surveyId': sid}).sort('version', 1)),
            list(db.question_definitions.find().sort('_id', 1)))


def test_atomic_save_success_and_explicit_null_deadline(clients, db):
    a, _, _ = clients; register(a, 'owner'); s = survey(a)
    a.patch('/api/surveys/'+s['_id'], json={'deadlineAt': '2030-01-01T00:00:00Z'})
    d = a.get(f"/api/surveys/{s['_id']}/draft").json()
    d['questions'] = [{'id': 'local', **content(), 'routingRules': []}]
    d['settings']['anonymous'] = False
    r = save(a, s, d, {'title': '  一起保存  ', 'description': '说明', 'deadlineAt': None, 'submissionPolicy': 'multiple'})
    assert r.status_code == 200, r.text
    result = r.json()
    assert result['survey']['title'] == '一起保存' and result['survey']['deadlineAt'] is None
    assert result['survey']['submissionPolicy'] == 'multiple'
    assert result['draft']['revision'] == 1 and result['draft']['settings']['anonymous'] is False
    persisted, versions, _ = documents(db, s)
    assert persisted['title'] == '一起保存' and versions[0]['questions'][0]['id'] == 'local'
    # Existing preview, publish and metadata-only editing stay available.
    assert a.get(f"/api/surveys/{s['_id']}/preview").status_code == 200
    publish(a, s, 1)
    frozen = deepcopy(db.survey_versions.find_one({'surveyId': persisted['_id']}))
    assert a.patch('/api/surveys/'+s['_id'], json={'title': '仅元信息'}).status_code == 200
    assert db.survey_versions.find_one({'_id': frozen['_id']}) == frozen


@pytest.mark.parametrize('reason,code', [('revision', 'DRAFT_CONFLICT'), ('content', 'SOURCE_MISMATCH'), ('private_source', 'NOT_FOUND')])
def test_atomic_save_rolls_back_metadata_on_draft_failure(clients, db, reason, code):
    a, b, _ = clients; register(a, 'owner'); register(b, 'reader')
    q = create_question(a); private = create_question(b); s = survey(a); d = imported(a, s, q)
    before = documents(db, s)
    if reason == 'revision': d['revision'] = 0
    if reason == 'content': d['questions'][0]['title'] = '假来源内容'
    if reason == 'private_source': d['questions'][0]['source']['questionId'] = private
    r = save(a, s, d, {'title': '绝不能部分保存', 'description': '新说明', 'deadlineAt': '2030-01-01T00:00:00Z',
        'submissionPolicy': 'multiple', 'statisticsContribution': True})
    assert r.json()['error']['code'] == code, r.text
    assert documents(db, s) == before  # Includes timestamps, writeRevision and source locks.


def test_atomic_save_rolls_back_after_both_writes(clients, db, monkeypatch):
    a, _, _ = clients; register(a, 'owner'); q = create_question(a); s = survey(a)
    d = a.get(f"/api/surveys/{s['_id']}/draft").json()
    d['questions'] = [{'id': 'linked', **content(), 'routingRules': [], 'source': {'questionId': q, 'questionVersion': 1}}]
    before = documents(db, s)
    original = SurveyService._edit
    def fail_after_write(self, *args, **kwargs):
        original(self, *args, **kwargs)
        raise DomainError('INJECTED_FAILURE', '故障注入', 409)
    monkeypatch.setattr(SurveyService, '_edit', fail_after_write)
    assert save(a, s, d).json()['error']['code'] == 'INJECTED_FAILURE'
    assert documents(db, s) == before


@pytest.mark.parametrize('guard', ['ownership', 'csrf', 'origin'])
def test_atomic_save_preserves_security_constraints(clients, db, guard):
    a, b, _ = clients; register(a, 'owner'); register(b, 'reader'); s = survey(a)
    d = a.get(f"/api/surveys/{s['_id']}/draft").json(); before = documents(db, s)
    body = {'metadata': {'title': '不应保存'}, 'draft': {'expectedRevision': 0, 'settings': d['settings'], 'questions': []}}
    client, headers = a, {}
    if guard == 'ownership': client = b
    if guard == 'csrf': headers['X-CSRF-Token'] = 'invalid'
    if guard == 'origin': headers['Origin'] = 'https://foreign.example'
    assert client.post(f"/api/surveys/{s['_id']}/save", json=body, headers=headers).status_code == 403
    assert documents(db, s) == before


def test_atomic_save_keeps_policy_lock_and_frozen_draft(clients, db):
    a, b, _ = clients; register(a, 'owner'); register(b, 'reader'); q = create_question(a); s = survey(a)
    d = imported(a, s, q); publish(a, s); answer(b, s, d['questions'][0]['id'], 18)
    before = documents(db, s)
    assert save(a, s, d).json()['error']['code'] == 'DRAFT_CONFLICT'
    assert documents(db, s) == before
    d = a.post(f"/api/surveys/{s['_id']}/draft-from-published").json(); before = documents(db, s)
    assert save(a, s, d, {'title': '锁定后不应变化', 'submissionPolicy': 'multiple'}).json()['error']['code'] == 'POLICY_LOCKED'
    assert documents(db, s) == before


def test_concurrent_atomic_saves_keep_matching_metadata_and_draft(clients, db):
    a, _, _ = clients; user = register(a, 'owner'); s = survey(a); svc = SurveyService(db)
    def worker(title):
        d = {'expectedRevision': 0, 'settings': {'anonymous': True},
             'questions': [{'id': 'local', **content(title=title), 'routingRules': []}]}
        try: return svc.save(s['_id'], user['id'], {'title': title}, d)['survey']['title']
        except DomainError as e: return e.code
    with ThreadPoolExecutor(2) as pool: results = list(pool.map(worker, ['A', 'B']))
    assert results.count('DRAFT_CONFLICT') == 1
    persisted, versions, _ = documents(db, s)
    assert persisted['title'] == versions[0]['questions'][0]['title']
    assert versions[0]['revision'] == 1 and persisted['writeRevision'] == 1


def test_active_filter_precedes_pagination_search_and_total(clients, db):
    a, b, _ = clients; owner = register(a, 'owner'); register(b, 'reader')
    qs = [create_question(a, content(title=f'page-{i:02}')) for i in range(23)]
    for q in qs: share(a, q, ['reader'])
    create_question(b, content(title='page-private'))  # Not part of A's or B's shared scope.
    ids = [ObjectId(q) for q in qs]
    db.question_definitions.update_many({'_id': {'$in': ids}}, {'$set': {'updatedAt': now()}})
    db.question_definitions.update_many({'_id': {'$in': ids[-10:]}}, {'$set': {'archived': True}})
    expected = list(reversed(qs[:-10]))
    for client, scope in [(a, 'mine'), (a, 'accessible'), (b, 'shared')]:
        query = {'search': 'page-', 'scope': scope, 'limit': 10}
        original = client.get('/api/questions', params=query).json()
        assert original['total'] == 23 and all(q['archived'] for q in original['items'])
        assert client.get('/api/questions', params={**query, 'activeOnly': False}).json() == original
        first = client.get('/api/questions', params={**query, 'activeOnly': True}).json()
        second = client.get('/api/questions', params={**query, 'activeOnly': True, 'offset': 10}).json()
        assert first['total'] == second['total'] == 13
        assert [q['_id'] for q in first['items'] + second['items']] == expected
        assert all(not q['archived'] for q in first['items'] + second['items'])
        assert client.get('/api/questions', params={**query, 'activeOnly': True, 'offset': 20}).json()['items'] == []
    assert a.get('/api/questions?activeOnly=true&search=absent').json()['total'] == 0


def test_survey_count_excludes_unused_submissions_and_deduplicates_surveys(clients):
    a, b, _ = clients; register(a, 'owner'); register(b, 'reader'); q = create_question(a)
    surveys = [survey(a), survey(a)]
    drafts = [imported(a, s, q) for s in surveys]
    for s in surveys: publish(a, s)
    result = stat(a, q)
    assert (result['surveyCount'], result['submissionCount'], result['answeredCount']) == (0, 0, 0)
    assert a.get(f'/api/questions/{q}/usage?version=1').json()['total'] == 2
    for value in (18, 30): answer(b, surveys[0], drafts[0]['questions'][0]['id'], value)
    result = stat(a, q, mode='historical_raw')
    assert (result['surveyCount'], result['submissionCount'], result['answeredCount']) == (1, 2, 2)


def test_survey_count_includes_submissions_that_skip_the_target(clients):
    a, b, _ = clients; register(a, 'owner'); register(b, 'reader'); q = create_question(a)
    s = survey(a); d = imported(a, s, q)
    trigger = {'id': 'trigger', **content(), 'routingRules': [{'id': 'end', 'priority': 1,
        'condition': {'operator': 'gte', 'operand': 0}, 'target': {'kind': 'end'}}]}
    d['questions'].insert(0, trigger)
    assert save(a, s, d).status_code == 200
    publish(a, s, 2); answer(b, s, 'trigger', 20)
    result = stat(a, q)
    assert (result['surveyCount'], result['submissionCount'], result['answeredCount']) == (1, 1, 0)
    assert result['mean'] is None


@pytest.mark.parametrize('replacement', ['new_version', 'unlinked_local'])
def test_survey_count_excludes_old_answers_replaced_across_versions(clients, replacement):
    a, b, _ = clients; register(a, 'owner'); register(b, 'reader'); q = create_question(a)
    s = survey(a); d = imported(a, s, q); local = d['questions'][0]['id']; publish(a, s)
    answer(b, s, local, 18)
    assert stat(a, q)['surveyCount'] == 1
    d = a.post(f"/api/surveys/{s['_id']}/draft-from-published").json()
    if replacement == 'new_version':
        assert a.post(f'/api/questions/{q}/versions', json={'content': content(title='新版'), 'parentVersion': 1, 'expectedCurrentVersion': 1}).status_code == 201
        d = imported(a, s, q, 2, 0, local)
    else:
        del d['questions'][0]['source']
        d['questions'][0]['title'] = '本地副本'
        assert save(a, s, d).status_code == 200
    publish(a, s, 1); answer(b, s, local, 60, 2)
    effective, raw = stat(a, q), stat(a, q, mode='historical_raw')
    assert (effective['surveyCount'], effective['submissionCount'], effective['answeredCount']) == (0, 0, 0)
    assert (raw['surveyCount'], raw['submissionCount'], raw['answeredCount']) == (1, 1, 1)
    assert a.get(f'/api/questions/{q}/usage?version=1').json()['total'] == 1
