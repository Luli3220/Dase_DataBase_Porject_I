$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
$env:PYTHONIOENCODING = 'utf-8'
& .\.venv\Scripts\python.exe -m pytest -q --junitxml=docs/evidence/final.xml
if ($LASTEXITCODE -ne 0) { throw 'Tests failed. Inspect pytest output.' }
