"""Package only source/config/docs/evidence; never include secrets or database files."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[2]
EXCLUDED={'.venv','.local','.git','.pytest_cache','__pycache__','delivery','test-results'}


def included(path):
    rel=path.relative_to(ROOT)
    return not any(part in EXCLUDED for part in rel.parts) and not path.suffix=='.pyc' and not (path.name.startswith('.env') and path.name!='.env.example')


def main():
    paths=sorted(p for p in ROOT.rglob('*') if p.is_file() and included(p))
    paths=[p for p in paths if p.name!='delivery-manifest.json']
    manifest={'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in paths],
              'excludes':sorted(EXCLUDED|{'.env','*.pyc'}),'note':'Source/docs/evidence only; recreate .venv/.env and initialize MongoDB using README.'}
    manifest_path=ROOT/'docs'/'delivery-manifest.json'
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    paths.append(manifest_path)
    output=ROOT/'delivery';output.mkdir(exist_ok=True)
    archive=output/'Project1-complete.zip'
    with ZipFile(archive,'w',ZIP_DEFLATED) as z:
        for p in paths:z.write(p,'Project1/'+p.relative_to(ROOT).as_posix())
    with ZipFile(archive) as z:
        assert z.testzip() is None
        assert not any('/.env' in name and not name.endswith('/.env.example') for name in z.namelist())
        assert not any(any('/'+part+'/' in name for part in EXCLUDED) for name in z.namelist())
        for entry in manifest['files']:
            assert hashlib.sha256(z.read('Project1/'+entry['path'])).hexdigest()==entry['sha256']
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    (output/'SHA256SUMS.txt').write_text(digest+'  '+archive.name+'\n',encoding='utf-8')
    print(json.dumps({'archive':str(archive),'files':len(paths),'bytes':archive.stat().st_size,'sha256':digest,'verified':True},ensure_ascii=False))


if __name__=='__main__':main()
