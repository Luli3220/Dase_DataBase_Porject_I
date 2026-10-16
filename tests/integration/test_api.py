from uuid import uuid4
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.db.mongo import now
from tests.fixtures import fixture_questions, answers

pytestmark = pytest.mark.integration
PASSWORD = "test-only-random!"  # Only synthetic per-test accounts; never a seeded production password.


@pytest.fixture
def clients(db, monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "test-only-" + "x" * 48)
    from app.main import create_app
    config = Settings(session_secret="test-only-" + "x" * 48, base_url="http://testserver")
    app = create_app(config, db)
    with TestClient(app) as a, TestClient(app) as b:
        yield a, b, app


def register(client, name):
    r = client.post("/api/auth/register", json={"username": name, "password": PASSWORD})
    assert r.status_code == 201, r.text
    client.headers["X-CSRF-Token"] = r.json()["csrfToken"]
    return r.json()["user"]


def make(client, anonymous=True, policy="latest_only"):
    r = client.post("/api/surveys", json={"title": "四题样例", "description": "测试", "anonymous": anonymous, "submissionPolicy": policy})
    assert r.status_code == 201, r.text
    s = r.json()
    edit = client.put(f"/api/surveys/{s['_id']}/draft", json={"expectedRevision": 0, "settings": {"anonymous": anonymous}, "questions": fixture_questions()})
    assert edit.status_code == 200, edit.text
    assert client.post(f"/api/surveys/{s['_id']}/publish", json={"expectedRevision": 1}).status_code == 200
    return s


def submit(client, s, version=1, **values):
    return client.post(f"/api/public/surveys/{s['publicId']}/submissions", json={"surveyVersion": version, "requestId": str(uuid4()), "answers": answers(**(values or {"q1": "no", "q3": 8}))})


def test_auth_and_csrf(clients, db):
    a, b, app = clients
    assert a.get('/api/me').status_code == 401
    user = register(a, "Test_A")
    assert user["username"] == "test_a"
    assert db.users.find_one({"username": "test_a"})["passwordHash"].startswith("$argon2id$")
    assert b.post('/api/auth/register', json={"username": "TEST_A", "password": PASSWORD}).status_code == 409
    assert b.post('/api/auth/login', json={"username": "test_a", "password": "wrong-password"}).status_code == 401
    assert a.post('/api/surveys', json={"title": "bad-origin"}, headers={"Origin": "https://evil.example"}).status_code == 403
    token = a.headers.pop('X-CSRF-Token')
    assert a.post('/api/surveys', json={"title": "no-token"}).status_code == 403
    a.headers['X-CSRF-Token'] = token
    assert a.post('/api/auth/logout').status_code == 200
    assert a.get('/api/me').status_code == 401
    login = a.post('/api/auth/login', json={"username": "test_a", "password": PASSWORD})
    assert login.status_code == 200
    assert 'HttpOnly' in login.headers['set-cookie'] and 'SameSite=lax' in login.headers['set-cookie']
    assert b.post('/api/auth/register', json={"username": {"$ne": None}, "password": PASSWORD}).status_code == 422


def test_api_chain_versions_anonymity(clients):
    a,b,_ = clients;register(a,"owner");u=register(b,"reader");s=make(a);base='/api/surveys/'+s['_id']
    p=submit(b,s);assert p.status_code==201,p.text
    assert submit(b,s,q1='yes',q2=['python','java'],q4='好课').status_code==201
    st=a.get(base+'/statistics').json();assert st['rawSubmissionCount']==2 and st['effectiveSubmissionCount']==1
    rows=a.get(base+'/submissions').json();assert rows['total']==2 and u['id'] not in str(rows) and 'respondentId' not in str(rows)
    one=a.get(base+'/questions/q2/statistics').json()['questions'][0];assert one==st['questions'][1]
    assert a.post(base+'/draft-from-published').status_code==200
    assert b.get('/api/public/surveys/'+s['publicId']).json()['surveyVersion']==1
    assert a.put(base+'/draft',json={'expectedRevision':0,'settings':{'anonymous':False},'questions':fixture_questions()}).status_code==200
    assert a.post(base+'/publish',json={'expectedRevision':1}).status_code==200
    assert submit(b,s).json()['error']['code']=='SURVEY_VERSION_CHANGED'
    assert submit(b,s,version=2).status_code==201
    assert a.get(base+'/statistics?version=1').json()['effectiveSubmissionCount']==0
    assert a.get(base+'/statistics?version=1&mode=historical_raw').json()['rawSubmissionCount']==2
    assert 'respondentId' not in a.get(base+'/submissions?version=1').text
    assert a.get(base+'/submissions?version=2').json()['items'][0]['respondentId']==u['id']
    assert a.post(base+'/close').status_code==200
    assert submit(b,s,version=2).json()['error']['code']=='SURVEY_CLOSED'
    assert a.get(base+'/statistics?version=1&mode=historical_raw').status_code==200


@pytest.mark.parametrize('path,method,body',[
    ('','GET',None),('','PATCH',{'title':'intrude'}),('/draft','GET',None),('/draft','PUT',{'expectedRevision':0,'settings':{'anonymous':True},'questions':fixture_questions()}),
    ('/versions','GET',None),('/publish','POST',{'expectedRevision':1}),('/close','POST',None),('/draft-from-published','POST',None),('/statistics','GET',None),('/submissions','GET',None),('/questions/q1/statistics','GET',None),('/preview','GET',None),
])
def test_ownership(clients,path,method,body):
    a,b,_=clients;register(a,'owner');register(b,'reader');s=make(a)
    response=b.request(method,'/api/surveys/'+s['_id']+path,json=body)
    assert response.status_code==403,response.text
    assert b.get('/api/surveys').json()['total']==0
    assert b.get('/api/public/surveys/'+s['publicId']).status_code==200


def test_invalid_statuses_and_serialization(clients,db):
    a,b,_=clients;register(a,'owner');register(b,'reader');s=make(a);base='/api/surveys/'+s['_id']
    assert a.get('/api/surveys/not-object-id').status_code==404
    assert a.get(base+'/statistics?mode=bad').status_code==422
    assert a.get(base+'/statistics?version=99').status_code==404
    assert a.get(base+'/questions/missing/statistics').status_code==404
    assert a.put(base+'/draft',json={'expectedRevision':1,'settings':{'anonymous':True},'questions':fixture_questions()}).status_code==409
    assert submit(b,s,q1='no',q3='8').status_code==422
    body={'surveyVersion':1,'requestId':str(uuid4()),'answers':answers(q1='no',q3=8),'respondentId':'forged'}
    r=b.post('/api/public/surveys/'+s['publicId']+'/submissions',json=body)
    assert r.status_code==422 and 'forged' not in r.text
    assert b.get('/api/me/submissions').json()['total']==0
    deadline=(now()+timedelta(days=1)).isoformat()
    r=a.patch(base,json={'deadlineAt':deadline});assert r.status_code==200,r.text
    assert r.json()['deadlineAt'].endswith('Z')
    assert a.patch(base,json={'deadlineAt':'2026-10-16T12:00:00'}).status_code==422
    assert a.patch(base,json={'title':None}).status_code==422
    r=a.patch(base,json={'deadlineAt':now().isoformat()});assert r.status_code==200,r.text
    assert submit(b,s).json()['error']['code']=='SURVEY_EXPIRED'


def test_session_expiry(clients,monkeypatch):
    a,_,_=clients
    import itsdangerous.timed
    original=itsdangerous.timed.TimestampSigner.get_timestamp
    with monkeypatch.context() as m:
        m.setattr(itsdangerous.timed.TimestampSigner,'get_timestamp',lambda self:original(self)-30000)
        register(a,'expired')
    assert a.get('/api/me').json()['error']['code']=='SESSION_EXPIRED'


def test_logout_revokes_copied_cookie(clients):
    a,b,_=clients;register(a,'owner')
    stolen=a.cookies.get('survey_session')
    assert a.post('/api/auth/logout').status_code==200
    b.cookies.set('survey_session',stolen)
    assert b.get('/api/me').json()['error']['code']=='SESSION_EXPIRED'


def test_body_size_limit_even_without_content_length(clients):
    a,_,_=clients
    r=a.post('/api/auth/login',content=b'x'*2_097_153,headers={'Content-Type':'application/json'})
    assert r.status_code==413
    r=a.post('/api/auth/login',content=(b'x'*65536 for _ in range(33)),headers={'Content-Type':'application/json'})
    assert r.status_code==413


def test_html_assets_openapi_and_preview(clients,db):
    a,_,_=clients;register(a,'owner');s=make(a);base='/api/surveys/'+s['_id']
    for path in ['/login','/register','/dashboard','/surveys/new','/surveys/'+s['_id']+'/edit','/survey/'+s['publicId'],'/surveys/'+s['_id']+'/statistics','/static/app.js','/static/style.css','/openapi.json','/docs']:
        assert a.get(path).status_code==200
    a.post(base+'/draft-from-published')
    before=db.submissions.count_documents({})
    assert a.get(base+'/preview').json()['questions'][0]['id']=='q1'
    assert db.submissions.count_documents({})==before
    assert a.get('/health').json()['status']=='ok'
