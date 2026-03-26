$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$env:Path = [Environment]::GetEnvironmentVariable("Path","User") + ";" + [Environment]::GetEnvironmentVariable("Path","Machine")
$env:NEXT_PUBLIC_API_BASE = "http://127.0.0.1:8011/api"

$backendCmd = "cd `"$root\backend`"; & `"$root\.venv\Scripts\Activate.ps1`"; python -m uvicorn main:app --reload --port 8011"
$frontendCmd = "cd `"$root\frontend`"; npm run dev"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Output "Started backend and frontend in separate PowerShell windows."
