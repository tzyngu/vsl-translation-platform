$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$ErrorActionPreference = "Continue"
$composeOutput = & docker compose up -d postgres 2>&1
$composeExitCode = $LASTEXITCODE
$ErrorActionPreference = "Stop"
if ($composeExitCode -ne 0) {
    $composeOutput | Out-Host
    throw "Cannot start PostgreSQL. Open Docker Desktop, wait until it is ready, then run this command again."
}

$composeOutput | Out-Host
for ($attempt = 1; $attempt -le 30; $attempt++) {
    if (Test-NetConnection -ComputerName "127.0.0.1" -Port 5432 -InformationLevel Quiet -WarningAction SilentlyContinue) {
        Write-Host "PostgreSQL is ready on 127.0.0.1:5432."
        exit 0
    }
    Start-Sleep -Seconds 1
}

throw "PostgreSQL container started but port 5432 was not ready after 30 seconds."
