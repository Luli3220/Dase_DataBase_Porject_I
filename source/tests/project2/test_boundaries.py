from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from bson import ObjectId
import pytest
from tests.integration.test_api import clients, register
from tests.project2.test_library import create_question, content, share
from tests.project2.test_import import survey, imported, publish
from app.services.questions import QuestionService
from app.services.surveys import SurveyService
from app.core.errors import DomainError


@pytest.mark.parametrize('endpoint', ['versions', 'restore', 'fork', 'usage', 'statistics?version=1'])
def test_private_endpoints_do_not_leak(clients, endpoint):
    a, b, _ = clients; register(a, 'owner'); register(b, 'reader'); q = create_question(a)
    path = f'/api/questions/{q}/{endpoint}'
    response = b.post(path, json={'version': 1, 'expectedCurrentVersion': 1}) if endpoint == 'restore' else b.post(path, json={'version': 1}) if endpoint == 'fork' else b.get(path)
    assert response.status_code == 404


def test_import_limits_invalid_versions_and_pinned_bank(clients):
    a, _, _ = clients; register(a, 'owner'); q = create_question(a); s = survey(a)
    qs = [{'id': 'q_'+str(i), **content(), 'routingRules': []} for i in range(100)]
    assert a.put(f"/api/surveys/{s['_id']}/draft", json={'expectedRevision': 0, 'settings': {'anonymous': True}, 'questions': qs}).status_code == 200
    r = a.post(f"/api/surveys/{s['_id']}/draft/import-question", json={'questionId': q, 'questionVersion': 1, 'expectedRevision': 1})
    assert r.status_code == 422
    assert a.post(f'/api/questions/{q}/restore', json={'version': 99, 'expectedCurrentVersion': 1}).status_code == 404
    b = a.post('/api/question-banks', json={'name': '固定旧版'}).json(); path = '/api/question-banks/'+b['_id']
    assert a.put(path+'/items', json={'questionId': q, 'pinnedVersion': 99, 'expectedRevision': 0}).status_code == 404
    assert a.put(path+'/items', json={'questionId': q, 'pinnedVersion': 1, 'expectedRevision': 0}).status_code == 200
    assert a.post(f'/api/questions/{q}/versions', json={'content': content(title='新题'), 'parentVersion': 1, 'expectedCurrentVersion': 1}).status_code == 201
    assert a.get(path).json()['items'][0]['resolvedVersion'] == 1


def test_revoke_import_race_is_serializable(clients, db):
    a, b, _ = clients; ua = register(a, 'owner'); ub = register(b, 'reader')
    q = create_question(a); share(a, q, ['reader']); s = survey(b)
    revision = a.get('/api/questions/'+q).json()['revision']
    def do_import():
        try: return SurveyService(db).import_question(s['_id'], ub['id'], q, 1, 0)['revision']
        except DomainError as e: return e.code
    def revoke():
        try: return QuestionService(db).sharing(q, ua['id'], [], revision)['ok']
        except DomainError as e: return e.code
    with ThreadPoolExecutor(2) as pool:
        importing, revoking = pool.submit(do_import), pool.submit(revoke)
        result, revoked = importing.result(), revoking.result()
    assert result in (1, 'NOT_FOUND')
    assert revoked in (True, 'VERSION_CONFLICT')
    # A revision conflict is an explicit unsuccessful revoke, followed by a fresh retry.
    share(a, q, [])
    assert b.get('/api/questions/'+q).status_code == 404
    if result == 1:
        publish(b, s)
        assert b.get('/api/public/surveys/'+s['publicId']).status_code == 200


def test_publish_import_race_keeps_snapshot_atomic(clients, db):
    a, _, _ = clients; u = register(a, 'owner'); q1, q2 = create_question(a), create_question(a)
    s = survey(a); imported(a, s, q1); svc = SurveyService(db)
    def run(operation):
        try: return operation()
        except DomainError as e: return e.code
    with ThreadPoolExecutor(2) as pool:
        edit = pool.submit(run, lambda: svc.import_question(s['_id'], u['id'], q2, 1, 1))
        sealing = pool.submit(run, lambda: svc.publish(s['_id'], u['id'], 1))
        results = [edit.result(), sealing.result()]
    assert sum(isinstance(r, dict) for r in results) == 1
    d = db.survey_versions.find_one({'surveyId': ObjectId(s['_id'])})
    assert (d['state'], len(d['questions']), d['revision']) in [('sealed', 1, 1), ('draft', 2, 2)]
