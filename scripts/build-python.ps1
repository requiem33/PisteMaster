# PowerShell script to build Python backend with PyInstaller
# Usage: .\scripts\build-python.ps1 [-Configuration Release]

param(
    [string]$Configuration = "Release"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"
$DistDir = Join-Path $BackendDir "dist"

Write-Host "Building Python backend..." -ForegroundColor Cyan
Write-Host "Configuration: $Configuration" -ForegroundColor Yellow
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Yellow
Write-Host "Backend Dir: $BackendDir" -ForegroundColor Yellow

# Create virtual environment if not exists
$VenvDir = Join-Path $BackendDir "venv_build"
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment"
        exit 1
    }
}

# Activate virtual environment
& "$VenvDir\Scripts\Activate.ps1"

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r "$BackendDir\requirements.txt"
pip install pyinstaller

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install dependencies"
    deactivate
    exit 1
}

# Build executable
Write-Host "Running PyInstaller..." -ForegroundColor Yellow
Set-Location $BackendDir
pyinstaller PisteMaster.spec --noconfirm --clean

if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build failed"
    deactivate
    exit 1
}

# Check result
$ExePath = Join-Path $DistDir "pistemaster-backend\pistemaster-backend.exe"
if (Test-Path $ExePath) {
    Write-Host "Build successful!" -ForegroundColor Green
    Write-Host "Output: $ExePath" -ForegroundColor Green
    Write-Host "Dist folder: $DistDir\pistemaster-backend" -ForegroundColor Green
} else {
    Write-Error "Build failed! Executable not found at $ExePath"
    deactivate
    exit 1
}

# Deactivate
deactivate

Write-Host "Done." -ForegroundColor Cyan