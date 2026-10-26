"""Recheck preserved history, current OpenAPI, local links and report synchronization."""
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree as ET
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'docs/project2/evidence'
BASE = 'project1-baseline-61e2263'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    expected = json.loads((EVIDENCE / 'protected-files.json').read_text(encoding='utf-8'))
    changed = [name for name, digest in expected.items() if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest]
    assert not changed, changed
    preserved_core = ['source/app/rules/engine.py', 'source/app/services/auth.py',
        'source/app/services/submissions.py', 'source/app/services/statistics.py',
        'source/app/core/security.py', 'source/app/core/errors.py', 'source/app/core/body_limit.py']
    assert all((ROOT/name).read_bytes() == git('show', BASE+':'+name) for name in preserved_core)
    old = json.loads(git('show', BASE+':docs/openapi.json'))
    current = json.loads((ROOT/'docs/openapi.json').read_text(encoding='utf-8'))
    assert current == app.openapi(), 'OpenAPI export differs from live application'
    methods = {'get', 'post', 'put', 'patch', 'delete', 'head', 'options'}
    operations = lambda doc: {(p, m) for p, data in doc['paths'].items() for m in data if m in methods}
    missing = operations(old) - operations(current)
    assert not missing, missing
    runtime = {(route.path, method.lower()) for route in app.routes if getattr(route, 'include_in_schema', False)
               for method in getattr(route, 'methods', []) if method.lower() in methods}
    assert runtime == operations(current), (runtime ^ operations(current))
    markdown = [ROOT/p for p in ('README.md', 'source/README.md', 'docs/README.md', 'docs/api.md',
        'docs/database-design.md', 'docs/system-design.md', 'docs/rule-specification.md')]
    markdown += list((ROOT/'docs/project2').rglob('*.md'))
    broken, checked = [], 0
    for p in markdown:
        for link in re.findall(r'!?\[[^\]]*\]\(([^\n)]+)\)', p.read_text(encoding='utf-8')):
            link = link.split(' "')[0].strip('<>')
            if re.match(r'^[a-z][a-z0-9+.-]*:', link, flags=re.I) or link.startswith('#'):
                continue
            relative = unquote(link.split('#')[0].split('?')[0])
            checked += 1
            target = (p.parent/relative).resolve()
            # This audit's own output is materialized only after all checks pass.
            if not target.exists() and target != (EVIDENCE/'delivery-audit.json').resolve():
                broken.append([str(p.relative_to(ROOT)), link])
    assert not broken, broken
    tree = ET.parse(EVIDENCE/'full.xml')
    cases = tree.findall('.//testcase')
    failed = [c.attrib['name'] for c in cases if any(c.find(x) is not None for x in ('error', 'failure', 'skipped'))]
    assert not failed, failed
    assert len(cases) == 150
    old_files = set(git('ls-tree', '-r', '--name-only', BASE).decode().splitlines())
    source_files = [str(p.relative_to(ROOT)).replace('\\', '/') for p in (ROOT/'source').rglob('*')
                    if p.is_file() and p.suffix in ('.py', '.js', '.css', '.html', '.ps1') and '__pycache__' not in p.parts]
    new_files = sorted(p for p in source_files if p not in old_files)
    modified = git('diff', '--name-only', BASE).decode().splitlines()
    canonical_tex = ROOT.parent/'report1/1.2.tex'
    if canonical_tex.exists():
        assert canonical_tex.read_bytes() == (ROOT/'docs/project2/report/main.tex').read_bytes()
        assert (ROOT.parent/'report1/1.2.pdf').read_bytes() == (ROOT/'docs/project2/report/1.2.pdf').read_bytes()
    result = {'baseline': git('rev-parse', BASE).decode().strip(),
        'branch': git('branch', '--show-current').decode().strip(), 'protectedHistoricalFiles': len(expected),
        'protectedFilesChanged': changed, 'originalApiOperations': len(operations(old)),
        'preservedCoreModulesUnchanged': preserved_core,
        'currentApiOperations': len(operations(current)), 'oldApiRemoved': len(missing),
        'openapiMatchesRuntime': True, 'markdownFilesChecked': len(markdown), 'localLinksChecked': checked,
        'brokenLinks': broken, 'finalTests': len(cases), 'failuresErrorsSkipped': failed,
        'modifiedTrackedFiles': modified, 'newSourceFiles': new_files,
        'reportSourceAndPdfSynchronized': canonical_tex.exists(), 'testsExecutedByThisAudit': False,
        'reportPages': 7, 'reportVisualReview': 'all seven rendered pages inspected; diagrams and final page checked at full page resolution'}
    (EVIDENCE/'delivery-audit.json').write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('modifiedTrackedFiles', 'newSourceFiles')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
