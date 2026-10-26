from uuid import uuid4
from copy import deepcopy
import pytest
from bson import ObjectId
from tests.integration.test_api import clients, register
from tests.project2.test_library import content, create_question, share
from tests.project2.test_import import survey, imported, publish


def answer(client, s, local_id, value, version=1):
    r = client.post('/api/public/surveys/'+s['publicId']+'/submissions', json={
        'surveyVersion': version, 'requestId': str(uuid4()), 'answers': [] if value is None else [{'questionId': local_id, 'value': value}]})
    assert r.status_code == 201, r.text


def stat(a, q, version=1, scope='mine', mode='current_effective'):
    r = a.get(f'/api/questions/{q}/statistics', params={'version': version, 'scope': scope, 'mode': mode})
    assert r.status_code == 200, r.text
    return r.json()


def test_number_distribution_exact_version_latest_across_versions(clients):
    a, b, _ = clients; register(a, 'owner'); register(b, 'reader'); q = create_question(a)
    s = survey(a); draft = imported(a, s, q); local = draft['questions'][0]['id']; publish(a, s)
    answer(b, s, local, 18); answer(b, s, local, 30)
    assert stat(a, q)['mean'] == 30
    assert stat(a, q, mode='historical_raw')['answeredCount'] == 2
    assert a.post(f'/api/questions/{q}/versions', json={'content': content(title='新版'), 'parentVersion': 1, 'expectedCurrentVersion': 1}).status_code == 201
    a.post(f"/api/surveys/{s['_id']}/draft-from-published")
    imported(a, s, q, 2, 0, local); publish(a, s)
    answer(b, s, local, 60, 2)
    assert stat(a, q, 1)['answeredCount'] == 0
    assert stat(a, q, 1, mode='historical_raw')['answeredCount'] == 2
    assert stat(a, q, 2)['mean'] == 60
    multi = survey(a, policy='multiple'); d = imported(a, multi, q); lid = d['questions'][0]['id']; publish(a, multi)
    values = [-1.5, 0, 17.9, 18, 30, 45, 60, 120, 121, 9007199254740991]
    for value in values: answer(b, multi, lid, value)
    result = stat(a, q)
    assert result['answeredCount'] == 10 and result['submissionCount'] == 10 and result['surveyCount'] == 1
    assert [x['count'] for x in result['distribution']] == [1, 2, 1, 1, 1, 2, 2]
    assert result['mean'] == pytest.approx(sum(values)/len(values))
    assert b.get(f'/api/questions/{q}/statistics?version=1').status_code == 404
    assert a.get(f'/api/questions/{q}/statistics').status_code == 422


@pytest.mark.parametrize('kind,values,counts', [('single_choice', ['a', 'b', 'a'], [2, 1]),
    ('multiple_choice', [['a', 'b'], ['b'], ['a']], [2, 2])])
def test_choice_across_surveys(clients, kind, values, counts):
    a, b, _ = clients; register(a, 'owner'); register(b, 'reader'); q = create_question(a, content(kind))
    for index, value in enumerate(values):
        s = survey(a, title=str(index)); d = imported(a, s, q); publish(a, s)
        answer(b, s, d['questions'][0]['id'], value)
    result = stat(a, q)
    assert result['surveyCount'] == 3 and result['answeredCount'] == 3
    assert [o['count'] for o in result['options']] == counts
    assert result['countUnit'].startswith('submission')


def test_cross_user_consent_suppression_revocation_and_text_privacy(clients):
    a, b, _ = clients; register(a, 'owner'); register(b, 'reader'); q = create_question(a, content('text'))
    share(a, q, ['reader']); s = survey(b, title='私密标题', policy='multiple'); d = imported(b, s, q); publish(b, s)
    for _ in range(2): answer(b, s, d['questions'][0]['id'], '敏感文本')
    assert stat(a, q)['answeredCount'] == 0
    assert stat(a, q, scope='consented_shared')['answeredCount'] == 0
    assert b.patch('/api/surveys/'+s['_id'], json={'statisticsContribution': True}).status_code == 200
    result = stat(a, q, scope='consented_shared')
    assert result['answeredCount'] == 0 and result['exclusions']['suppressedSurveyCount'] == 1
    answer(b, s, d['questions'][0]['id'], '敏感文本')
    result = stat(a, q, scope='consented_shared')
    assert result['answeredCount'] == 3
    assert all(secret not in str(result) for secret in ['敏感文本', s['_id'], 'respondentId', '用户名', '私密标题'])
    assert b.patch('/api/surveys/'+s['_id'], json={'statisticsContribution': False}).status_code == 200
    assert stat(a, q, scope='consented_shared')['answeredCount'] == 0


def test_usage_visibility_elem_match_and_skipped_answers(clients):
    a, b, _ = clients; register(a, 'owner'); register(b, 'reader')
    optional = {**content(), 'required': False}; q = create_question(a, optional); q2 = create_question(a)
    a.post(f'/api/questions/{q}/versions', json={'content': optional, 'parentVersion': 1, 'expectedCurrentVersion': 1})
    a.post(f'/api/questions/{q2}/versions', json={'content': content(), 'parentVersion': 1, 'expectedCurrentVersion': 1})
    s = survey(a); imported(a, s, q); d = imported(a, s, q2, 2, 1)
    # q/v1 and q2/v2 in separate elements must not match q/v2.
    assert a.get(f'/api/questions/{q}/usage?version=2').json()['total'] == 0
    share(a, q, ['reader'])
    assert b.get(f'/api/questions/{q}/usage').json()['total'] == 0
    first = d['questions'][0]
    first['routingRules'] = [{'id': 'skip', 'priority': 1, 'condition': {'operator': 'gte', 'operand': 0}, 'target': {'kind': 'end'}}]
    a.put(f"/api/surveys/{s['_id']}/draft", json={'expectedRevision': 2, 'settings': d['settings'], 'questions': d['questions']})
    publish(a, s, 3)
    answer(b, s, first['id'], 2)
    assert stat(a, q2, 2)['submissionCount'] == 1 and stat(a, q2, 2)['answeredCount'] == 0
    assert stat(a, q2, 2)['mean'] is None
    assert sum(x['count'] for x in stat(a, q2, 2)['distribution']) == 0
    assert b.get(f'/api/questions/{q}/usage').json()['total'] == 1
    a.post(f"/api/surveys/{s['_id']}/draft-from-published")
    usages = a.get(f'/api/questions/{q}/usage').json()
    assert {x['status'] for x in usages['items']} == {'draft', 'published'}
    assert b.get(f'/api/questions/{q}/usage').json()['total'] == 1
    a.post(f"/api/surveys/{s['_id']}/close")
    assert b.get(f'/api/questions/{q}/usage').json()['total'] == 0


def test_usage_index_explain_and_migration(db):
    from scripts.migrate_project2 import migrate
    from app.db.mongo import now
    db.users.insert_one({'username': 'legacy', 'passwordHash': 'synthetic', 'createdAt': now(), 'schemaVersion': 1})
    before = deepcopy(db.users.find_one())
    assert migrate(db)['oldDocumentsUnchanged'] and migrate(db)['oldDocumentsUnchanged']
    assert db.users.find_one() == before
    query = {'questions': {'$elemMatch': {'source.questionId': ObjectId(), 'source.questionVersion': 1}}}
    # This Windows Mongo build emits a non-UTF8 hostname in explain.serverInfo.
    # Replacement decoding is restricted to diagnostics, never application data reads.
    from bson.codec_options import CodecOptions
    diagnostics = db.with_options(codec_options=CodecOptions(unicode_decode_error_handler='replace'))
    explained = diagnostics.command('explain', {'find': 'survey_versions', 'filter': query,
        'hint': 'questions.source.questionId_1_questions.source.questionVersion_1'}, verbosity='executionStats',
        codec_options=CodecOptions(unicode_decode_error_handler='replace'))
    assert 'IXSCAN' in str(explained['queryPlanner'])
