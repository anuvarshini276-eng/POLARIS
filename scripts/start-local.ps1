$ErrorActionPreference = 'Stop'
$polarisRoot = Split-Path $PSScriptRoot -Parent
$polarisPython = Join-Path $polarisRoot '.venv\Scripts\python.exe'
try {
    $polarisRunning = Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/health' -TimeoutSec 2
    if ($polarisRunning.status -eq 'ok') { Write-Output 'http://localhost:8000'; return }
} catch { }
if (!(Test-Path $polarisPython)) { python -m venv (Join-Path $polarisRoot '.venv') }
Push-Location $polarisRoot
& $polarisPython -m pip install -r backend/requirements.txt
Push-Location frontend
npm.cmd ci
npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' }
Pop-Location
& $polarisPython scripts/seed_database.py
& $polarisPython scripts/seed_media.py
$env:PYTHONPATH = Join-Path $polarisRoot 'backend'
Start-Process -FilePath $polarisPython -ArgumentList '-m','app.workers.run' -WorkingDirectory $polarisRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $polarisRoot 'data\worker.log') -RedirectStandardError (Join-Path $polarisRoot 'data\worker-error.log')
Start-Process -FilePath $polarisPython -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $polarisRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $polarisRoot 'data\server.log') -RedirectStandardError (Join-Path $polarisRoot 'data\server-error.log')
Pop-Location
Write-Output 'http://localhost:8000'
