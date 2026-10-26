from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from bson import ObjectId
import pytest
from tests.integration.test_api import clients, register
from app.core.errors import DomainError
from app.services.questions import QuestionService
from app.services.question_banks import QuestionBankService


def content(kind='number', title='你的年龄'):
    return {'type': kind, 'title': title, 'required': True,
            'options': [{'id': 'a', 'label': '甲'}, {'id': 'b', 'label': '乙'}] if 'choice' in kind else [], 'validation': {}}


def create_question(client, value=None):
    r = client.post('/api/questions', json={'content': value or content()})
    assert r.status_code == 201, r.text
    return r.json()['definition']['_id']


@pytest.mark.parametrize('kind', ['number', 'text', 'single_choice', 'multiple_choice'])
def test_four_types(clients, kind):
    a, b, _ = clients; register(a, 'owner'); register(b, 'reader')
    q = create_question(a, content(kind))
    row = a.get('/api/questions/'+q).json()
    assert row['current']['content'] == content(kind)
    assert b.get('/api/questions/'+q).status_code == 404
    assert a.get('/api/questions?search=年龄&scope=mine').json()['total'] == 1
    assert a.get('/api/questions?search=.*').json()['total'] == 0
    assert a.get('/api/questions?offset=1').json()['items'] == []


@pytest.mark.parametrize('change', [
    {'title': ' '}, {'type': 'unknown'}, {'validation': {'min': 5, 'max': 2}},
    {'validation': {'integerOnly': 'yes'}}, {'options': [{'id': 'a', 'label': '非法'}]}, {'routingRules': []},
    {'validation': {'min': True}}, {'validation': {'min': 1e100}}])
def test_bad_config(clients, change):
    a, _, _ = clients; register(a, 'owner')
    assert a.post('/api/questions', json={'content': {**content(), **change}}).status_code == 422


def test_lineage_restore_fork_and_conflict(clients, db):
    a, b, _ = clients; owner = register(a, 'owner'); register(b, 'reader')
    q = create_question(a)
    old = deepcopy(db.question_versions.find_one({'questionId': ObjectId(q)}))
    for expected, parent in [(1, 1), (2, 1)]:
        r = a.post(f'/api/questions/{q}/versions', json={'content': content(title=f'第{expected+1}版'),
            'parentVersion': parent, 'expectedCurrentVersion': expected})
        assert r.status_code == 201, r.text
        assert r.json()['parentVersion'] == parent
    assert a.post(f'/api/questions/{q}/versions', json={'content': content(), 'parentVersion': 1, 'expectedCurrentVersion': 1}).status_code == 409
    restored = a.post(f'/api/questions/{q}/restore', json={'version': 1, 'expectedCurrentVersion': 3})
    assert restored.status_code == 201
    assert restored.json()['version'] == 4 and restored.json()['restoredFromVersion'] == 1
    assert db.question_versions.find_one({'_id': old['_id']}) == old
    assert a.get(f'/api/questions/{q}/versions?limit=2').json()['total'] == 4
    fork = a.post(f'/api/questions/{q}/fork', json={'version': 2}).json()
    assert fork['definition']['_id'] != q
    assert fork['definition']['forkedFrom'] == {'questionId': q, 'questionVersion': 2}
    assert fork['version']['content']['title'] == '第2版'
    assert b.post(f'/api/questions/{q}/fork', json={'version': 1}).status_code == 404
    assert owner['id'] == str(old['createdBy'])


def share(a, q, users):
    row = a.get('/api/questions/'+q).json()
    r = a.patch(f'/api/questions/{q}/sharing', json={'usernames': users, 'expectedRevision': row['revision']})
    assert r.status_code == 200, r.text


def test_sharing_permissions_banks_and_revocation(clients, db):
    a, b, _ = clients; register(a, 'owner'); register(b, 'reader'); q = create_question(a)
    assert a.patch(f'/api/questions/{q}/sharing', json={'usernames': ['missing'], 'expectedRevision': 0}).status_code == 422
    share(a, q, ['READER', 'reader'])
    assert b.get('/api/questions?scope=shared').json()['total'] == 1
    assert 'sharedUsernames' not in b.get('/api/questions/'+q).json()
    assert b.patch(f'/api/questions/{q}/sharing', json={'usernames': [], 'expectedRevision': 1}).status_code == 403
    assert b.post(f'/api/questions/{q}/restore', json={'version': 1, 'expectedCurrentVersion': 1}).status_code == 403
    banks = [b.post('/api/question-banks', json={'name': '常用题'}).json() for _ in range(2)]
    for bank in banks:
        path = '/api/question-banks/'+bank['_id']
        add = b.put(path+'/items', json={'questionId': q, 'pinnedVersion': 1, 'expectedRevision': 0})
        assert add.status_code == 200, add.text
        assert a.get(path).status_code == 404
        assert b.put(path+'/items', json={'questionId': q, 'expectedRevision': 0}).status_code == 409
        assert b.put(path+'/items', json={'questionId': q, 'expectedRevision': 1}).status_code == 200
        assert len(b.get(path).json()['items']) == 1
    a.post(f'/api/questions/{q}/versions', json={'content': content(title='新年龄'), 'parentVersion': 1, 'expectedCurrentVersion': 1})
    assert b.get('/api/question-banks/'+banks[0]['_id']).json()['items'][0]['resolvedVersion'] == 2
    share(a, q, [])
    assert b.get('/api/questions/'+q).status_code == 404
    assert b.get('/api/question-banks/'+banks[0]['_id']).json()['items'][0] == {'questionId': q, 'available': False}
    assert b.delete('/api/question-banks/'+banks[0]['_id']+'/items/'+q+'?expectedRevision=2').status_code == 200
    assert db.question_versions.count_documents({'questionId': ObjectId(q)}) == 2
    bank = banks[1]
    assert b.patch('/api/question-banks/'+bank['_id'], json={'name': '改名', 'description': '内容', 'expectedRevision': 2}).status_code == 200


def test_concurrent_append_and_bank_cas(db):
    uid = db.users.insert_one({'username': 'owner', 'passwordHash': 'synthetic', 'schemaVersion': 1,
        'createdAt': __import__('app.db.mongo', fromlist=['now']).now()}).inserted_id
    svc = QuestionService(db); q = svc.create(uid, content())['definition']['_id']
    def append(_):
        try: return svc.append(q, uid, 1, 1, content())['version']
        except DomainError as e: return e.code
    with ThreadPoolExecutor(2) as pool: results = list(pool.map(append, range(2)))
    assert sorted(map(str, results)) == ['2', 'VERSION_CONFLICT']
    assert db.question_versions.count_documents({'questionId': q}) == 2
    banks = QuestionBankService(db); bank = banks.create(uid, '题库')
    def add(_):
        try: return banks.member(bank['_id'], uid, 0, q)['revision']
        except DomainError as e: return e.code
    with ThreadPoolExecutor(2) as pool: results = list(pool.map(add, range(2)))
    assert sorted(map(str, results)) == ['1', 'BANK_CONFLICT']


def test_library_csrf_origin_and_owner_injection(clients):
    a, _, _ = clients; register(a, 'owner')
    assert a.post('/api/questions', json={'content': content(), 'ownerId': str(ObjectId())}).status_code == 422
    assert a.post('/api/questions', json={'content': content()}, headers={'Origin': 'https://foreign.example'}).status_code == 403
    token = a.headers.pop('X-CSRF-Token')
    assert a.post('/api/questions', json={'content': content()}).status_code == 403
    a.headers['X-CSRF-Token'] = token
