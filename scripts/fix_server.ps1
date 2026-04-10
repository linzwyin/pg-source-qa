# Fix CLI on server - Run this on your Windows server

$ErrorActionPreference = "Stop"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Fixing pg-qa CLI" -ForegroundColor Cyan
Write-Host "=============================================="

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host ""
Write-Host "Project root: $ProjectRoot"

# Step 1: Check Python
Write-Host ""
Write-Host "Step 1: Checking Python..." -ForegroundColor Yellow
try {
    $PythonVersion = python --version 2>&1
    Write-Host "Python: $PythonVersion"
} catch {
    Write-Host "python not found" -ForegroundColor Red
    exit 1
}

# Step 2: Activate virtual environment
Write-Host ""
Write-Host "Step 2: Activating virtual environment..." -ForegroundColor Yellow

$VenvPaths = @(".venv", "venv")
$Activated = $false

foreach ($Venv in $VenvPaths) {
    $ActivateScript = Join-Path $ProjectRoot "$Venv\Scripts\Activate.ps1"
    if (Test-Path $ActivateScript) {
        & $ActivateScript
        Write-Host "Activated $Venv"
        $Activated = $true
        break
    }
}

if (-not $Activated) {
    Write-Host "Virtual environment not found! Creating..." -ForegroundColor Red
    python -m venv .venv
    . .venv\Scripts\Activate.ps1
}

Write-Host "Python path: $(Get-Command python).Source"

# Step 3: Uninstall old version
Write-Host ""
Write-Host "Step 3: Uninstalling old version..." -ForegroundColor Yellow
pip uninstall pg-source-qa -y 2>$null
if ($?) {
    Write-Host "Uninstalled old version"
}

# Step 4: Reinstall
Write-Host ""
Write-Host "Step 4: Reinstalling package..." -ForegroundColor Yellow
pip install -e ".[dev]"

# Step 5: Check generated scripts
Write-Host ""
Write-Host "Step 5: Checking generated scripts..." -ForegroundColor Yellow

$ScriptsDir = ".venv\Scripts"
$PgQaExe = Join-Path $ScriptsDir "pg-qa.exe"
$PgQaScript = Join-Path $ScriptsDir "pg-qa-script.py"

if (Test-Path $PgQaExe) {
    Write-Host "✓ pg-qa.exe found" -ForegroundColor Green
} else {
    Write-Host "✗ pg-qa.exe not found" -ForegroundColor Red
}

if (Test-Path $PgQaScript) {
    Write-Host "✓ pg-qa-script.py found" -ForegroundColor Green
    Get-Content $PgQaScript -TotalCount 5 | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "✗ pg-qa-script.py not found" -ForegroundColor Red
}

# Step 6: Test import
Write-Host ""
Write-Host "Step 6: Testing import..." -ForegroundColor Yellow

try {
    $ImportTest = python -c "from source_qa.cli import app; print('OK')" 2>&1
    if ($ImportTest -eq "OK") {
        Write-Host "✓ Import successful" -ForegroundColor Green
    } else {
        throw "Import failed"
    }
} catch {
    Write-Host "✗ Import failed, trying with PYTHONPATH..." -ForegroundColor Yellow
    $Env:PYTHONPATH = "$ProjectRoot\src;$Env:PYTHONPATH"
    $ImportTest = python -c "from source_qa.cli import app; print('OK')" 2>&1
    if ($ImportTest -eq "OK") {
        Write-Host "✓ Import successful with PYTHONPATH" -ForegroundColor Green
    } else {
        Write-Host "✗ Still failing" -ForegroundColor Red
    }
}

# Step 7: Test CLI
Write-Host ""
Write-Host "Step 7: Testing CLI..." -ForegroundColor Yellow

$PgQaPath = Get-Command pg-qa -ErrorAction SilentlyContinue
if ($PgQaPath) {
    Write-Host "✓ pg-qa in PATH: $($PgQaPath.Source)" -ForegroundColor Green
    Write-Host "Running: pg-qa --help"
    try {
        pg-qa --help
        Write-Host "✓ CLI working!" -ForegroundColor Green
    } catch {
        Write-Host "✗ CLI failed" -ForegroundColor Red
    }
} else {
    Write-Host "✗ pg-qa not in PATH" -ForegroundColor Red
    Write-Host "Trying direct path..." -ForegroundColor Yellow
    
    if (Test-Path $PgQaExe) {
        try {
            & $PgQaExe --help
            Write-Host "✓ CLI working (direct path)!" -ForegroundColor Green
        } catch {
            Write-Host "✗ CLI failed" -ForegroundColor Red
        }
    }
}

# Step 8: Alternative test
Write-Host ""
Write-Host "Step 8: Alternative test (python -m)..." -ForegroundColor Yellow
try {
    python -m source_qa.cli --help
    Write-Host "✓ Module execution working!" -ForegroundColor Green
} catch {
    Write-Host "✗ Module execution failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Fix script complete" -ForegroundColor Cyan
Write-Host "=============================================="
Write-Host ""
Write-Host "If CLI still not working, try:"
Write-Host "  `$env:PYTHONPATH = '$ProjectRoot\src;' + `$env:PYTHONPATH"
Write-Host "  python -m source_qa.cli --help"
Write-Host ""
