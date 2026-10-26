from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from bson import ObjectId
from tests.integration.test_api import clients, register
from tests.project2.test_library import create_question, content, share
from app.services.surveys import SurveyService
from app.core.errors import DomainError


def survey(a, title='复用问卷', policy='latest_only'):
    r = a.post('/api/surveys', json={'title': title, 'submissionPolicy': policy})
    assert r.status_code == 201, r.text
    return r.json()


def imported(a, s, q, version=1, revision=0, replace=None):
    r = a.post(f"/api/surveys/{s['_id']}/draft/import-question", json={
        'questionId': q, 'questionVersion': version, 'expectedRevision': revision, 'replaceLocalId': replace})
    assert r.status_code == 200, r.text
    return r.json()


def publish(a, s, revision=1):
    r = a.post(f"/api/surveys/{s['_id']}/publish", json={'expectedRevision': revision})
    assert r.status_code == 200, r.text
    return r.json()


def test_snapshots_sources_upgrade_detach_and_archive(clients, db):
    a, b, _ = clients; register(a, 'owner'); register(b, 'reader')
    q = create_question(a); share(a, q, ['reader'])
    sa, sb = survey(a), survey(b)
    da, dbb = imported(a, sa, q), imported(b, sb, q)
    qa, qb = da['questions'][0], dbb['questions'][0]
    assert qa['source'] == qb['source'] and qa['id'] != qb['id']
    assert isinstance(db.survey_versions.find_one({'surveyId': ObjectId(sa['_id'])})['questions'][0]['source']['questionId'], ObjectId)
    assert a.get(f"/api/surveys/{sa['_id']}/preview").status_code == 200
    assert a.post(f"/api/surveys/{sa['_id']}/draft/import-question", json={
        'questionId': q, 'questionVersion': 1, 'expectedRevision': 1}).status_code == 422
    assert b.post(f"/api/surveys/{sa['_id']}/draft/import-question", json={
        'questionId': q, 'questionVersion': 1, 'expectedRevision': 1}).status_code == 403
    publish(a, sa); publish(b, sb)
    frozen = deepcopy(db.survey_versions.find_one({'surveyId': ObjectId(sb['_id']), 'version': 1}))
    assert a.post(f'/api/questions/{q}/versions', json={'content': content(title='年龄新版'), 'parentVersion': 1, 'expectedCurrentVersion': 1}).status_code == 201
    share(a, q, [])
    assert b.get('/api/public/surveys/'+sb['publicId']).json()['questions'][0]['title'] == '你的年龄'
    assert db.survey_versions.find_one({'_id': frozen['_id']}) == frozen
    assert b.post(f"/api/surveys/{sb['_id']}/draft-from-published").status_code == 200
    # Existing linked snapshots remain saveable after access revocation.
    draft = b.get(f"/api/surveys/{sb['_id']}/draft").json()
    body = {'expectedRevision': 0, 'settings': draft['settings'], 'questions': draft['questions']}
    assert b.put(f"/api/surveys/{sb['_id']}/draft", json=body).status_code == 200
    body['expectedRevision'] = 1; body['questions'][0]['title'] = '篡改来源'
    assert b.put(f"/api/surveys/{sb['_id']}/draft", json=body).json()['error']['code'] == 'SOURCE_MISMATCH'
    del body['questions'][0]['source']
    assert b.put(f"/api/surveys/{sb['_id']}/draft", json=body).status_code == 200
    assert a.post(f"/api/surveys/{sa['_id']}/draft-from-published").status_code == 200
    upgraded = imported(a, sa, q, 2, 0, qa['id'])
    assert upgraded['questions'][0]['source']['questionVersion'] == 2
    assert upgraded['questions'][0]['routingRules'] == []
    detail = a.get('/api/questions/'+q).json()
    assert a.patch(f'/api/questions/{q}/archive', json={'archived': True, 'expectedRevision': detail['revision']}).status_code == 200
    sc = survey(a)
    assert a.post(f"/api/surveys/{sc['_id']}/draft/import-question", json={'questionId': q, 'questionVersion': 1, 'expectedRevision': 0}).status_code == 409
    assert db.survey_versions.find_one({'_id': frozen['_id']}) == frozen


def test_source_forgery_duplicate_and_routing_decoupled(clients):
    a, b, _ = clients; register(a, 'owner'); register(b, 'reader')
    q = create_question(a); s = survey(b)
    forged = {'id': 'fake', **content(), 'routingRules': [], 'source': {'questionId': q, 'questionVersion': 1}}
    body = {'expectedRevision': 0, 'settings': {'anonymous': True}, 'questions': [forged]}
    assert b.put(f"/api/surveys/{s['_id']}/draft", json=body).status_code == 404
    share(a, q, ['reader'])
    forged['routingRules'] = [{'id': 'end', 'priority': 1, 'condition': {'operator': 'gte', 'operand': 18}, 'target': {'kind': 'end'}}]
    assert b.put(f"/api/surveys/{s['_id']}/draft", json=body).status_code == 200
    body['expectedRevision'] = 1
    body['questions'].append({**deepcopy(forged), 'id': 'other'})
    assert b.put(f"/api/surveys/{s['_id']}/draft", json=body).status_code == 422
    assert a.get(f'/api/questions/{q}/versions').json()['items'][0]['content'].get('routingRules') is None


def test_import_concurrency_and_stale_retry(clients, db):
    a, _, _ = clients; user = register(a, 'owner'); q1, q2 = create_question(a), create_question(a)
    s = survey(a); svc = SurveyService(db)
    def run(q):
        try: return svc.import_question(s['_id'], user['id'], q, 1, 0)['revision']
        except DomainError as e: return e.code
    with ThreadPoolExecutor(2) as pool: results = list(pool.map(run, [q1, q2]))
    assert sorted(map(str, results)) == ['1', 'DRAFT_CONFLICT']
    draft = a.get(f"/api/surveys/{s['_id']}/draft").json()
    used = draft['questions'][0]['source']['questionId']
    remaining = q2 if used == q1 else q1
    assert len(imported(a, s, remaining, revision=1)['questions']) == 2
    publish(a, s, 2)
    assert a.post(f"/api/surveys/{s['_id']}/draft/import-question", json={'questionId': q1, 'questionVersion': 1, 'expectedRevision': 2}).status_code == 409
