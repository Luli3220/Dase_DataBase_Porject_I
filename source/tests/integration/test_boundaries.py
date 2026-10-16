from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4
import pytest
from bson import ObjectId
from app.core.errors import DomainError
from app.db.mongo import now
from app.services.surveys import SurveyService
from app.services.submissions import SubmissionService
from app.services.statistics import StatisticsService
from tests.fixtures import fixture_questions, answers
from tests.integration.test_core import published, payload

pytestmark=pytest.mark.integration


def test_concurrent_draft_revision_and_publish(db):
    svc=SurveyService(db);owner=ObjectId();s=svc.create(owner,{'title':'CAS'})
    def edit(_):
        try:
            return svc.edit(s['_id'],owner,{'expectedRevision':0,'settings':{'anonymous':True},'questions':fixture_questions()})['revision']
        except DomainError as e:return e.code
    with ThreadPoolExecutor(4) as pool:results=list(pool.map(edit,range(4)))
    assert results.count(1)==1 and results.count('DRAFT_CONFLICT')==3
    def publish(_):
        try:return svc.publish(s['_id'],owner,1)['publishedVersion']
        except DomainError as e:return e.code
    with ThreadPoolExecutor(4) as pool:results=list(pool.map(publish,range(4)))
    assert 1 in results and set(results)<={1,'DRAFT_CONFLICT'}
    assert svc.public(s['publicId'])[1]['state']=='sealed'


def test_publish_interruption_preserves_old_public_and_close_wins(db):
    s,owner=published(db);svc=SurveyService(db);svc.derive(s['_id'],owner)
    def crash():raise RuntimeError('fault after seal')
    with pytest.raises(RuntimeError):svc.publish(s['_id'],owner,0,after_seal=crash)
    assert svc.public(s['publicId'])[1]['version']==1
    svc.close(s['_id'],owner)
    with pytest.raises(DomainError) as e:svc.publish(s['_id'],owner,0)
    assert e.value.code=='SURVEY_CLOSED'
    assert db.surveys.find_one({'_id':s['_id']})['publishedVersion']==1


def test_failed_submission_does_not_lock_policy(db):
    s,owner=published(db);svc=SurveyService(db);subs=SubmissionService(db)
    with pytest.raises(DomainError):subs.submit(s['publicId'],ObjectId(),payload(q1='no'))
    assert not db.surveys.find_one({'_id':s['_id']})['hasSubmissions']
    assert svc.patch(s['_id'],owner,{'submissionPolicy':'multiple'})['submissionPolicy']=='multiple'


def test_policy_change_and_first_submission_race(db):
    s,owner=published(db);svc=SurveyService(db);subs=SubmissionService(db);uid=ObjectId()
    def change():
        try:return svc.patch(s['_id'],owner,{'submissionPolicy':'multiple'})['submissionPolicy']
        except DomainError as e:return e.code
    with ThreadPoolExecutor(2) as pool:
        submitted=pool.submit(subs.submit,s['publicId'],uid,payload())
        changed=pool.submit(change)
        assert submitted.result()['id']
        policy_result=changed.result()
    doc=db.surveys.find_one({'_id':s['_id']})
    assert doc['hasSubmissions'] and policy_result in ('multiple','POLICY_LOCKED')
    assert doc['submissionPolicy']==('multiple' if policy_result=='multiple' else 'latest_only')
    with pytest.raises(DomainError):svc.patch(s['_id'],owner,{'submissionPolicy':'latest_only' if doc['submissionPolicy']=='multiple' else 'multiple'})


@pytest.mark.parametrize('action',['close','publish'])
def test_submission_state_race(db,action):
    s,owner=published(db);svc=SurveyService(db);subs=SubmissionService(db)
    if action=='publish':svc.derive(s['_id'],owner)
    def submit():
        try:return subs.submit(s['publicId'],ObjectId(),payload())
        except DomainError as e:return e.code
    with ThreadPoolExecutor(2) as pool:
        result=pool.submit(submit)
        change=pool.submit(svc.close,s['_id'],owner) if action=='close' else pool.submit(svc.publish,s['_id'],owner,0)
        change.result();r=result.result()
    assert isinstance(r,dict) or r==('SURVEY_CLOSED' if action=='close' else 'SURVEY_VERSION_CHANGED')
    if isinstance(r,dict):assert db.submissions.find_one({'_id':ObjectId(r['id'])})['surveyVersion']==1
    with pytest.raises(DomainError):subs.submit(s['publicId'],ObjectId(),payload())


def test_tie_breaker_pagination_and_numeric_text_samples(db):
    s,owner=published(db);subs=SubmissionService(db);stats=StatisticsService(db);uid=ObjectId()
    ids=[]
    for n in range(3):
        p=payload(q1='no',q3=10+n,q4=f'回答{n}')
        ids.append(ObjectId(subs.submit(s['publicId'],uid,p)['id']))
    stamp=now()-timedelta(days=1)
    db.submissions.update_many({'surveyId':s['_id']},{'$set':{'submittedAt':stamp}})
    st=stats.statistics(s['_id'],owner)
    latest=db.submissions.find_one({'_id':max(ids)})
    assert st['questions'][2]['mean']==latest['answers'][1]['value']
    historical=stats.statistics(s['_id'],owner,mode='historical_raw',offset=1,limit=1)
    assert historical['questions'][2]['mean']==11 and len(historical['questions'][2]['values'])==1
    assert historical['questions'][3]['values']==['回答1']
    row=subs.list_owner(s['_id'],owner,offset=1,limit=1)
    assert row['total']==3 and len(row['items'])==1
    for q in historical['questions']:
        assert stats.statistics(s['_id'],owner,mode='historical_raw',question_id=q['questionId'],offset=1,limit=1)['questions'][0]==q


def test_multiple_same_user_all_count_and_idempotent_after_close(db):
    s,owner=published(db,'multiple');subs=SubmissionService(db);uid=ObjectId()
    p=payload();one=subs.submit(s['publicId'],uid,p)
    subs.submit(s['publicId'],uid,payload())
    assert StatisticsService(db).statistics(s['_id'],owner)['effectiveSubmissionCount']==2
    SurveyService(db).close(s['_id'],owner)
    assert subs.submit(s['publicId'],uid,p)['id']==one['id']  # replay does not create a new submission
    with pytest.raises(DomainError):subs.submit(s['publicId'],uid,payload())
