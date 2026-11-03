param(
    [switch]$SkipStart,
    [int]$Port = 8000,
    [int]$TimeoutSeconds = 45
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $repoRoot "backend"
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$systemPython = "python"
$baseUrl = "http://localhost:$Port"

function Test-HttpEndpoint {
    param(
        [string]$Url,
        [string]$Method = "GET",
        [object]$Body = $null,
        [string]$ContentType = "application/json",
        [int[]]$AllowedStatusCodes = @(200)
    )

    try {
        if ($null -eq $Body) {
            $response = Invoke-WebRequest -Uri $Url -Method $Method -TimeoutSec 30 -SkipHttpErrorCheck
        }
        else {
            $response = Invoke-WebRequest -Uri $Url -Method $Method -Body $Body -ContentType $ContentType -TimeoutSec 30 -SkipHttpErrorCheck
        }

        $statusCode = [int]$response.StatusCode
        if ($statusCode -in $AllowedStatusCodes) {
            $jsonContent = $null
            try { $jsonContent = $response.Content | ConvertFrom-Json -Depth 10 } catch { $jsonContent = $response.Content }
            return @{ Success = $true; StatusCode = $statusCode; Data = $jsonContent }
        }

        $jsonContent = $null
        try { $jsonContent = $response.Content | ConvertFrom-Json -Depth 10 } catch { $jsonContent = $response.Content }
        return @{ Success = $false; StatusCode = $statusCode; Data = $jsonContent; Error = "HTTP status $statusCode" }
    }
    catch {
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

function Write-CheckResult {
    param(
        [string]$Name,
        [bool]$Passed
    )

    $status = if ($Passed) { "PASS" } else { "FAIL" }
    Write-Host ("[{0}] {1}" -f $status, $Name)
}

function Get-PythonExe {
    if (Test-Path $venvPython) {
        return $venvPython
    }
    return $systemPython
}

$pythonExe = Get-PythonExe

if (-not $SkipStart) {
$probe = Test-HttpEndpoint -Url "$baseUrl/api/health" -Method "GET"
    if (-not $probe.Success) {
    Write-Host "Starting backend on $baseUrl ..."
    $proc = Start-Process -FilePath $pythonExe -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port $Port --reload" -WorkingDirectory $backendDir -PassThru -WindowStyle Hidden
        if (-not $proc) {
            throw "Failed to start backend process."
        }
    }
    else {
    Write-Host "Backend already responding on $baseUrl"
    }

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
    $probe = Test-HttpEndpoint -Url "$baseUrl/api/health" -Method "GET"
        if ($probe.Success) { break }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)

    if (-not $probe.Success) {
        Write-CheckResult -Name "Backend startup" -Passed $false
    Write-Error "Backend did not respond within $TimeoutSeconds seconds. Please free port $Port or rerun with -Port <available_port>."
        exit 1
    }

    Write-CheckResult -Name "Backend startup" -Passed $true
}

$failures = 0

$checks = @()

# 1. Health route
$checks += @{ Name = "GET /api/health"; Action = { Test-HttpEndpoint -Url "$baseUrl/api/health" } }
$checks += @{ Name = "GET /api/system/info"; Action = { Test-HttpEndpoint -Url "$baseUrl/api/system/info" } }

# 2. Telemetry creation + retrieval
$telemetryBody = @{
    engine_id = "rotax914-uav-01"
    timestamp = (Get-Date).ToString("o")
    rpm = 5200
    egt_c = 700
    cht_c = 120
    oil_pressure_bar = 4.1
    oil_temperature_c = 90
    fuel_flow_lph = 18.4
    vibration_g = 0.24
    altitude_ft = 9500
    ambient_temperature_c = 12
    throttle = 65
    engine_load = 0.7
    power_kw = 52
} | ConvertTo-Json -Compress

$checks += @{ Name = "POST /api/telemetry"; Action = { Test-HttpEndpoint -Url "$baseUrl/api/telemetry" -Method "POST" -Body $telemetryBody } }
$checks += @{ Name = "GET /api/telemetry/rotax914-uav-01"; Action = { Test-HttpEndpoint -Url "$baseUrl/api/telemetry/rotax914-uav-01" } }
$checks += @{ Name = "GET /api/telemetry/latest"; Action = { Test-HttpEndpoint -Url "$baseUrl/api/telemetry/latest" } }

# 3. Engine & health
$checks += @{ Name = "GET /api/engine/rotax914-uav-01/state"; Action = { Test-HttpEndpoint -Url "$baseUrl/api/engine/rotax914-uav-01/state" } }
$checks += @{ Name = "GET /api/health/rotax914-uav-01"; Action = { Test-HttpEndpoint -Url "$baseUrl/api/health/rotax914-uav-01" -AllowedStatusCodes @(200, 404) } }

# 4. Fault routes
$checks += @{ Name = "GET /api/fault/status"; Action = { Test-HttpEndpoint -Url "$baseUrl/api/fault/status" } }
$faultActivateBody = @{ engine_id = "rotax914-uav-01"; fault_type = "OVERHEATING"; severity = 0.5 } | ConvertTo-Json -Compress
$checks += @{ Name = "POST /api/fault/activate"; Action = { Test-HttpEndpoint -Url "$baseUrl/api/fault/activate" -Method "POST" -Body $faultActivateBody } }
$checks += @{ Name = "GET /api/faults/rotax914-uav-01"; Action = { Test-HttpEndpoint -Url "$baseUrl/api/faults/rotax914-uav-01" } }
$faultDeactivateBody = @{ engine_id = "rotax914-uav-01" } | ConvertTo-Json -Compress
$checks += @{ Name = "POST /api/fault/deactivate"; Action = { Test-HttpEndpoint -Url "$baseUrl/api/fault/deactivate" -Method "POST" -Body $faultDeactivateBody } }

# 5. Predictions / RUL
$checks += @{ Name = "GET /api/predictions/rotax914-uav-01"; Action = { Test-HttpEndpoint -Url "$baseUrl/api/predictions/rotax914-uav-01" -AllowedStatusCodes @(200, 404) } }
$checks += @{ Name = "GET /api/rul/rotax914-uav-01"; Action = { Test-HttpEndpoint -Url "$baseUrl/api/rul/rotax914-uav-01" -AllowedStatusCodes @(200, 404) } }

# 6. Mission routes
$missionBody = @{
    engine_id = "rotax914-uav-01"
    duration_hours = 8
    altitude_ft = 12000
    ambient_temperature_c = 38
    throttle = 65
    mission_type = "SURVEILLANCE"
} | ConvertTo-Json -Compress
$missionCreate = Test-HttpEndpoint -Url "$baseUrl/api/mission/simulate" -Method "POST" -Body $missionBody
$missionId = $null
if ($missionCreate.Success) {
    $missionId = $missionCreate.Data.mission_id
    if (-not $missionId) { $missionId = $missionCreate.Data.id }
}

$checks += @{ Name = "POST /api/mission/simulate"; Action = { return $missionCreate } }
if ($missionId) {
    $checks += @{ Name = "GET /api/mission/$missionId"; Action = { Test-HttpEndpoint -Url "$baseUrl/api/mission/$missionId" } }
    $checks += @{ Name = "GET /api/replay/$missionId"; Action = { Test-HttpEndpoint -Url "$baseUrl/api/replay/$missionId" } }
}
else {
    $checks += @{ Name = "GET /api/mission/[mission_id]"; Action = { @{ Success = $false; Error = "No mission_id returned from POST /api/mission/simulate" } } }
    $checks += @{ Name = "GET /api/replay/[mission_id]"; Action = { @{ Success = $false; Error = "No mission_id returned from POST /api/mission/simulate" } } }
}

# 7. Maintenance advisory
$checks += @{ Name = "GET /api/maintenance/rotax914-uav-01"; Action = { Test-HttpEndpoint -Url "$baseUrl/api/maintenance/rotax914-uav-01" } }

# 8. WebSocket check via TestClient
$checks += @{ Name = "WS /ws/telemetry/rotax914-uav-01"; Action = {
        $code = @'
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
with client.websocket_connect('/ws/telemetry/rotax914-uav-01') as ws:
    payload = ws.receive_json()
    assert isinstance(payload, dict)
    assert payload.get('engine_id') == 'rotax914-uav-01'
    assert 'telemetry' in payload
    assert 'health' in payload
    assert 'fault' in payload
    print('WS_OK')
'@
        $out = & $pythonExe -c $code 2>&1
        if ($LASTEXITCODE -eq 0) { return @{ Success = $true; Data = $out } }
        return @{ Success = $false; Error = ($out | Out-String) }
    } }

# 9. Database sanity check
$checks += @{ Name = "Database check"; Action = {
        $code = @'
from app.models.database import SessionLocal
from app.models.engine import EngineModel
from app.models.telemetry import TelemetryModel
from app.models.fault import FaultRecordModel

db = SessionLocal()
try:
    engine_count = db.query(EngineModel).count()
    telemetry_count = db.query(TelemetryModel).count()
    fault_count = db.query(FaultRecordModel).count()
    print(f'ENGINE_COUNT={engine_count}; TELEMETRY_COUNT={telemetry_count}; FAULT_COUNT={fault_count}')
finally:
    db.close()
'@
        $out = & $pythonExe -c $code 2>&1
        if ($LASTEXITCODE -eq 0) { return @{ Success = $true; Data = $out } }
        return @{ Success = $false; Error = ($out | Out-String) }
    } }

foreach ($check in $checks) {
    $result = & $check.Action
    $passed = $result.Success
    Write-CheckResult -Name $check.Name -Passed $passed
    if (-not $passed) {
        $failures++
        if ($result.ContainsKey('Error')) {
            Write-Host "  Error: $($result.Error)"
        }
    }
    else {
        $payload = if ($result.ContainsKey('Data')) { $result.Data } else { $null }
        if ($payload) {
            if ($payload -is [string]) {
                $s = $payload.ToString().Trim()
                if ($s.Length -gt 0) {
                    Write-Host "  Response: $s"
                }
            }
            elseif ($payload -is [System.Collections.IDictionary] -or $payload -is [pscustomobject]) {
                $summary = ($payload | ConvertTo-Json -Depth 6 -Compress)
                if ($summary.Length -gt 0) { Write-Host "  Response: $summary" }
            }
        }
    }
}

if ($failures -gt 0) {
    Write-Host "`nBackend verification failed: $failures checks did not pass."
    exit 1
}

Write-Host "`nBackend verification passed for all routes and DB checks."
