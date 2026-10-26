$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
$PreviousEvidenceDir = $env:TEST_EVIDENCE_DIR
try {
$env:PYTHONIOENCODING = 'utf-8'
$env:TEST_EVIDENCE_DIR = '../docs/project2/evidence/full-browser'
New-Item -ItemType Directory -Force ../docs/project2/evidence | Out-Null
& ..\.venv\Scripts\python.exe -m pytest -q --junitxml=../docs/project2/evidence/full.xml
if ($LASTEXITCODE -ne 0) { throw 'Tests failed. Inspect pytest output.' }
} finally {
    $env:TEST_EVIDENCE_DIR = $PreviousEvidenceDir
    Pop-Location
}
