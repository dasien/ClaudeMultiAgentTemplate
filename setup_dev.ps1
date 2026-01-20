# CMAT Development Environment Setup Script (Windows PowerShell)
# This script ensures all dependencies are installed for CMAT to run

$ErrorActionPreference = "Stop"

Write-Host "=== CMAT Development Setup ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "Detected OS: Windows" -ForegroundColor Green
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found $pythonVersion" -ForegroundColor Green

    # Extract version number
    $versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
    if ($versionMatch) {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]

        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
            Write-Host "ERROR: Python 3.10 or higher is required. Found Python $major.$minor" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "ERROR: Python not found. Please install Python 3.10 or higher from python.org" -ForegroundColor Red
    Write-Host "Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Check tkinter
Write-Host "Checking tkinter installation..." -ForegroundColor Yellow
$tkinterCheck = python -c "import tkinter" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "tkinter is already installed." -ForegroundColor Green
} else {
    Write-Host "tkinter is NOT installed." -ForegroundColor Red
    Write-Host ""
    Write-Host "On Windows, tkinter should come with the standard Python installer." -ForegroundColor Yellow
    Write-Host "Please reinstall Python from python.org and ensure 'tcl/tk and IDLE' is selected." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "WARNING: CMAT GUI will not work without tkinter." -ForegroundColor Red
}
Write-Host ""

# Check venv module
Write-Host "Checking for venv module..." -ForegroundColor Yellow
$venvCheck = python -c "import venv" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python venv module is not installed." -ForegroundColor Red
    Write-Host "Please reinstall Python from python.org with all components." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "venv module is available." -ForegroundColor Green
}
Write-Host ""

# Create virtual environment if it doesn't exist
Write-Host "Setting up virtual environment..." -ForegroundColor Yellow
if (-Not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv

    # Verify it was created
    if (-Not (Test-Path ".venv\Scripts\activate")) {
        Write-Host "ERROR: Failed to create virtual environment." -ForegroundColor Red
        Write-Host "The venv directory may be incomplete. Try removing it and running again:" -ForegroundColor Yellow
        Write-Host "  Remove-Item -Recurse -Force .venv" -ForegroundColor Yellow
        Write-Host "  .\setup_dev.ps1" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Green
    # Verify existing venv is valid
    if (-Not (Test-Path ".venv\Scripts\activate")) {
        Write-Host "ERROR: Existing .venv directory is invalid (missing Scripts\activate)." -ForegroundColor Red
        Write-Host "Remove it and run again:" -ForegroundColor Yellow
        Write-Host "  Remove-Item -Recurse -Force .venv" -ForegroundColor Yellow
        Write-Host "  .\setup_dev.ps1" -ForegroundColor Yellow
        exit 1
    }
}
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"
Write-Host ""

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host ""

# Install package in development mode
Write-Host "Installing CMAT in development mode..." -ForegroundColor Yellow
pip install -e ".[dev]"
Write-Host ""

# Verify installation
Write-Host "=== Verifying Installation ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "Checking required packages..." -ForegroundColor Yellow
python -c "import yaml; print('  pyyaml: OK')"
python -c "from PIL import Image; print('  pillow: OK')"
python -c "import chromadb; print('  chromadb: OK')"
python -c "from sentence_transformers import SentenceTransformer; print('  sentence-transformers: OK')"

$tkinterFinalCheck = python -c "import tkinter" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  tkinter: OK" -ForegroundColor Green
} else {
    Write-Host "  tkinter: MISSING (GUI will not work)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "To activate the virtual environment in the future, run:" -ForegroundColor Yellow
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "If you get execution policy errors, run:" -ForegroundColor Yellow
Write-Host "  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor White
Write-Host ""
Write-Host "To launch CMAT, run:" -ForegroundColor Yellow
Write-Host "  cmat" -ForegroundColor White
Write-Host "  # or: python -m ui.main" -ForegroundColor White
Write-Host ""