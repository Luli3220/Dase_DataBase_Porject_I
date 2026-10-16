"""Explicit development seeding; prints generated credentials once, never writes them to files."""
import secrets
from app.core.config import Settings
from app.core.errors import require
from app.db.mongo import client_for, initialize
from app.services.auth import AuthService
from app.services.surveys import SurveyService
from tests.fixtures import fixture_questions

if __name__=='__main__':
    cfg=Settings()
    require(cfg.environment=='development' and cfg.mongo_db.endswith('_dev'), '只允许显式 development 且数据库名以 _dev 结尾', status=400)
    with client_for(cfg.mongo_uri) as client:
        db=client[cfg.mongo_db];initialize(db)
        owner=None
        for role in ('owner','reader'):
            name=role+'_'+secrets.token_hex(4);password=secrets.token_urlsafe(18)
            user=AuthService(db).register(name,password)
            if role=='owner':owner=user
            print(f'{role}: {name} / {password}')
        svc=SurveyService(db)
        s=svc.create(owner['_id'],{'title':'学习体验调查 · 四题演示','description':'匿名、重复填写与跳题规则示例。'})
        svc.edit(s['_id'],owner['_id'],{'expectedRevision':0,'settings':{'anonymous':True},'questions':fixture_questions()})
        svc.publish(s['_id'],owner['_id'],1)
        print(cfg.base_url+'/survey/'+s['publicId'])
