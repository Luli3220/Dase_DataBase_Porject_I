$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
$env:PYTHONIOENCODING = 'utf-8'
& ..\.venv\Scripts\python.exe -m pytest -q --junitxml=../docs/evidence/final.xml
if ($LASTEXITCODE -ne 0) { throw 'Tests failed. Inspect pytest output.' }
} finally {
    Pop-Location
}
