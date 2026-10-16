param([string]$MongoExe = 'F:\MongoDB\bin\mongod.exe', [int]$Port = 27018)
$ErrorActionPreference = 'Stop'
$ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$DataPath = Join-Path $ProjectRoot '.local\mongo'
New-Item -ItemType Directory -Force -Path $DataPath | Out-Null
$LogPath = Join-Path $ProjectRoot '.local\mongod.log'
$Connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if (-not $Connection) {
    Start-Process -FilePath $MongoExe -ArgumentList @('--dbpath', ('"' + $DataPath + '"'), '--port', "$Port", '--bind_ip', '127.0.0.1', '--replSet', 'rs0', '--logpath', ('"' + $LogPath + '"'), '--logappend') -WindowStyle Hidden
}
& (Join-Path $ProjectRoot '.venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'init_replica.py') --port $Port
if ($LASTEXITCODE -ne 0) { throw 'Mongo initialization failed' }
