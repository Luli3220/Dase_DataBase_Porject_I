"""A real HTTP demo, with freshly generated synthetic accounts (no saved credentials)."""
import json
import secrets
import os
from uuid import uuid4
import httpx
from tests.fixtures import fixture_questions, answers


def main():
    base = os.getenv("DEMO_BASE_URL", "http://127.0.0.1:8000")
    report = []
    with httpx.Client(base_url=base, timeout=20) as a, httpx.Client(base_url=base, timeout=20) as b:
        def call(client, method, path, expected=200, **kwargs):
            r=client.request(method,path,**kwargs)
            assert r.status_code==expected,(path,r.status_code,r.text)
            report.append({"method":method,"path":path,"status":r.status_code})
            return r.json()
        for client,role in [(a,'owner'),(b,'reader')]:
            name=role+'_'+secrets.token_hex(5);password=secrets.token_urlsafe(20)
            call(client,'POST','/api/auth/register',201,json={'username':name,'password':password})
            result=call(client,'POST','/api/auth/login',json={'username':name,'password':password})
            client.headers['X-CSRF-Token']=result['csrfToken']
        s=call(a,'POST','/api/surveys',201,json={'title':'HTTP真实演示 '+uuid4().hex[:8],'description':'匿名、版本和重复填写验收','anonymous':True})
        root='/api/surveys/'+s['_id'];public='/api/public/surveys/'+s['publicId']
        call(a,'PUT',root+'/draft',json={'expectedRevision':0,'settings':{'anonymous':True},'questions':fixture_questions()})
        published=call(a,'POST',root+'/publish',json={'expectedRevision':1})
        call(b,'GET',public)
        first={'surveyVersion':1,'requestId':str(uuid4()),'answers':answers(q1='no',q3=8)}
        first_result=call(b,'POST',public+'/submissions',201,json=first)
        assert call(b,'POST',public+'/submissions',201,json=first)['id']==first_result['id']
        call(b,'POST',public+'/submissions',201,json={'surveyVersion':1,'requestId':str(uuid4()),'answers':answers(q1='yes',q2=['python','java'],q4='希望增加示例')})
        st=call(a,'GET',root+'/statistics');assert st['rawSubmissionCount']==2 and st['effectiveSubmissionCount']==1
        raw=call(a,'GET',root+'/submissions');assert raw['total']==2 and 'respondentId' not in str(raw)
        call(b,'GET',root+'/statistics',403)
        call(a,'POST',root+'/draft-from-published')
        assert call(b,'GET',public)['surveyVersion']==1
        call(a,'POST',root+'/publish',json={'expectedRevision':0})
        conflict=call(b,'POST',public+'/submissions',409,json={'surveyVersion':1,'requestId':str(uuid4()),'answers':answers(q1='no',q3=8)})
        assert conflict['error']['code']=='SURVEY_VERSION_CHANGED'
        assert call(a,'GET',root+'/statistics?version=1&mode=historical_raw')['rawSubmissionCount']==2
        call(a,'POST',root+'/close')
        closed=call(b,'POST',public+'/submissions',409,json={'surveyVersion':2,'requestId':str(uuid4()),'answers':answers(q1='no',q3=8)})
        assert closed['error']['code']=='SURVEY_CLOSED'
        call(a,'POST','/api/auth/logout')
    print(json.dumps({'baseUrl':base,'checks':len(report),'result':'PASS','publicUrl':published['publicUrl'],'steps':report},ensure_ascii=False,indent=2))


if __name__=='__main__': main()
