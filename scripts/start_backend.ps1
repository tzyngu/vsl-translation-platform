$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
& ".\scripts\ensure_postgres.ps1"
& ".\.venv\Scripts\python.exe" -m uvicorn deploy.backend.main:app --host 127.0.0.1 --port 8001 --reload
