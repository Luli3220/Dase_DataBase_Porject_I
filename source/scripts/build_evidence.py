"""Build the test result index and environment metadata from JUnit output."""
import json
import argparse
import platform
import subprocess
from datetime import datetime, timezone, timedelta
from importlib.metadata import version
from pathlib import Path
from xml.etree import ElementTree as ET
from app.core.config import Settings
from app.db.mongo import client_for

ROOT=Path(__file__).resolve().parents[2]


def main():
    folder=ROOT/'docs'/'evidence'
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index-only',action='store_true',help='Only index existing JUnit; do not query MongoDB or rewrite environment/OpenAPI')
    args=parser.parse_args()
    report=folder/'respondent-username'/'full.xml'
    tree=ET.parse(report)
    cases=tree.findall('.//testcase')
    counts={'PASS':0,'FAIL':0,'SKIP':0}
    lines=['# 逐项测试结果','',f'来源：[完整JUnit](respondent-username/full.xml)，共{len(cases)}个测试实例。表中列出测试名称、结果和耗时，详细步骤见[测试用例](../test-cases.md)。','','|编号|测试（源模块/名称）|实际结果|耗时秒|','|---|---|---|---|']
    for i,c in enumerate(cases,1):
        status='SKIP' if c.find('skipped') is not None else 'FAIL' if c.find('failure') is not None or c.find('error') is not None else 'PASS'
        counts[status]+=1
        name=c.attrib['name'].replace('|','\\|')
        lines.append(f"|T{i:03}|{c.attrib['classname']}::{name}|{status}|{c.attrib['time']}|")
    (folder/'case-results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if args.index_only:
        print(json.dumps({'report':str(report),'tests':len(cases),'counts':counts,'testsExecuted':False},ensure_ascii=False))
        return
    cfg=Settings()
    with client_for(cfg.mongo_uri) as client:
        mongo=client.server_info()['version']
    git = subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True)
    meta={'recordedAt':datetime.now(timezone(timedelta(hours=8))).isoformat(),'timezone':'Asia/Shanghai','python':platform.python_version(),
          'platform':platform.platform(),'mongoVersion':mongo,'git':git.stdout.strip() if git.returncode == 0 else 'No Git repository in supplied workspace',
          'packages':{n:version(n) for n in ['fastapi','starlette','pymongo','pydantic','pytest','playwright','argon2-cffi','uvicorn']},
          'counts':counts,'tests':len(cases),'workingDirectory':'source','command':'../.venv/Scripts/python.exe -m pytest -q --junitxml=../docs/evidence/respondent-username/full.xml'}
    (folder/'environment.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    from app.main import app
    (ROOT/'docs'/'openapi.json').write_text(json.dumps(app.openapi(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(meta,ensure_ascii=False))


if __name__=='__main__':main()
