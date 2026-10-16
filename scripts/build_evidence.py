"""Build reproducible evidence indices from actual JUnit output; never fabricate passes."""
import json
import platform
from datetime import datetime, timezone, timedelta
from importlib.metadata import version
from pathlib import Path
from xml.etree import ElementTree as ET
from app.core.config import Settings
from app.db.mongo import client_for

ROOT=Path(__file__).resolve().parents[1]


def main():
    folder=ROOT/'docs'/'evidence'
    tree=ET.parse(folder/'final.xml')
    cases=tree.findall('.//testcase')
    counts={'PASS':0,'FAIL':0,'SKIP':0}
    lines=['# 逐项真实执行结果','','来源：final.xml；每个参数化实例独立记录。测试步骤、输入与断言在对应测试源文件，业务摘要见 ../test-cases.md。','','|编号|测试（源模块/名称）|实际结果|耗时秒|','|---|---|---|---|']
    for i,c in enumerate(cases,1):
        status='SKIP' if c.find('skipped') is not None else 'FAIL' if c.find('failure') is not None or c.find('error') is not None else 'PASS'
        counts[status]+=1
        name=c.attrib['name'].replace('|','\\|')
        lines.append(f"|T{i:03}|{c.attrib['classname']}::{name}|{status}|{c.attrib['time']}|")
    (folder/'case-results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    cfg=Settings()
    with client_for(cfg.mongo_uri) as client:
        mongo=client.server_info()['version']
    meta={'recordedAt':datetime.now(timezone(timedelta(hours=8))).isoformat(),'timezone':'Asia/Shanghai','python':platform.python_version(),
          'platform':platform.platform(),'mongoVersion':mongo,'git':'No Git repository in supplied workspace',
          'packages':{n:version(n) for n in ['fastapi','starlette','pymongo','pydantic','pytest','playwright','argon2-cffi','uvicorn']},
          'counts':counts,'tests':len(cases),'command':'.venv/Scripts/python.exe -m pytest -q --junitxml=docs/evidence/final.xml'}
    (folder/'environment.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    from app.main import app
    (ROOT/'docs'/'openapi.json').write_text(json.dumps(app.openapi(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(meta,ensure_ascii=False))


if __name__=='__main__':main()
