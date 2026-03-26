$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$env:Path = [Environment]::GetEnvironmentVariable("Path","User") + ";" + [Environment]::GetEnvironmentVariable("Path","Machine")
$env:NEXT_PUBLIC_API_BASE = "http://127.0.0.1:8011/api"
$env:API_BASE = "http://127.0.0.1:8011/api"

function Stop-Port {
    param([int]$Port)
    $lines = netstat -ano | findstr ":$Port"
    if ($lines) {
        $lines | ForEach-Object {
            $parts = ($_ -split "\s+") | Where-Object { $_ -ne "" }
            $procId = $parts[-1]
            if ($procId -match "^\d+$") {
                taskkill /PID $procId /F | Out-Null
            }
        }
    }
}

Stop-Port 8011
taskkill /IM python.exe /F | Out-Null

$db = Join-Path $root "backend\ticketing.db"
if (Test-Path $db) {
    $attempts = 0
    while ($attempts -lt 5) {
        try {
            Remove-Item $db -Force
            break
        } catch {
            Start-Sleep -Milliseconds 400
            $attempts++
        }
    }
}

$backendCmd = "cd `"$root\backend`"; & `"$root\.venv\Scripts\Activate.ps1`"; python -m uvicorn main:app --reload --port 8011"
$frontendCmd = "cd `"$root\frontend`"; npm run dev"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Start-Sleep -Seconds 2

# Wait for backend to be ready
$ready = $false
for ($i = 0; $i -lt 25; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8011/api/analytics/summary" -UseBasicParsing -TimeoutSec 2
        if ($resp.StatusCode -eq 200) { $ready = $true; break }
    } catch {
        Start-Sleep -Milliseconds 400
    }
}

Set-Location $root
if ($ready) {
    python seed_demo.py
} else {
    Write-Output "Backend not ready yet. Seed skipped. Run: python seed_demo.py"
}

Write-Output "Demo started. Backend: http://127.0.0.1:8011, Frontend: http://localhost:3000 or 3001"
