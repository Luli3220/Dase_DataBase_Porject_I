param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
& $Python -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11+ required'"
if ($LASTEXITCODE -ne 0) { throw 'Choose a Python 3.11+ interpreter with -Python.' }
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    & $Python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed' }
}
& .\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
if (-not (Test-Path -LiteralPath '.env')) {
    & .\.venv\Scripts\python.exe -c "from pathlib import Path; import secrets; p=Path('.env.example').read_text(encoding='utf-8'); Path('.env').write_text(p.replace('replace-with-python-secrets-token-url-safe-48', secrets.token_urlsafe(48)),encoding='utf-8')"
}
Write-Host 'Environment ready. Start MongoDB replica set, then python -m scripts.init_db and uvicorn.'
