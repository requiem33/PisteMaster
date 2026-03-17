#!/bin/bash
# Bash script to build Python backend with PyInstaller
# Usage: ./scripts/build-python.sh [--configuration Release]

set -e

CONFIGURATION="${1:-Release}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
DIST_DIR="$BACKEND_DIR/dist"

echo "Building Python backend..."
echo "Configuration: $CONFIGURATION"
echo "Project Root: $PROJECT_ROOT"
echo "Backend Dir: $BACKEND_DIR"

# Create virtual environment if not exists
VENV_DIR="$BACKEND_DIR/venv_build"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r "$BACKEND_DIR/requirements.txt"
pip install pyinstaller

# Build executable
echo "Running PyInstaller..."
cd "$BACKEND_DIR"
pyinstaller PisteMaster.spec --noconfirm --clean

# Check result
if [ -f "$DIST_DIR/pistemaster-backend/pistemaster-backend" ]; then
    echo "Build successful!"
    echo "Output: $DIST_DIR/pistemaster-backend/pistemaster-backend"
    echo "Dist folder: $DIST_DIR/pistemaster-backend"
else
    echo "Build failed! Executable not found"
    deactivate
    exit 1
fi

# Deactivate
deactivate

echo "Done."