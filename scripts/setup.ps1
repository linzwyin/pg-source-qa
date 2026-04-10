# Setup script for Source Code QA System
# Run this script to set up the development environment

$ErrorActionPreference = "Stop"

Write-Host "Setting up Source Code QA System..." -ForegroundColor Green

# Check Python version
$pythonVersion = python --version 2>&1
Write-Host "Python version: $pythonVersion"

# Create virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -e ".[dev]"

# Create .kimi.toml from example if it doesn't exist
if (-not (Test-Path ".kimi.toml")) {
    Write-Host "Creating .kimi.toml from example..." -ForegroundColor Yellow
    Copy-Item ".kimi.toml.example" ".kimi.toml"
    Write-Host "Please edit .kimi.toml and add your Moonshot API key" -ForegroundColor Cyan
}

# Create .env from example if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit .kimi.toml and add your Moonshot API key"
Write-Host "2. Run 'source-qa --help' to see available commands"
Write-Host "3. Run 'source-qa index <directory>' to index your code"
