$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
& ".\scripts\ensure_postgres.ps1"
& ".\.venv\Scripts\python.exe" deploy\frontend\manage.py migrate
& ".\.venv\Scripts\python.exe" deploy\frontend\manage.py runserver 127.0.0.1:8000
