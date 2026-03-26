#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Frontend检查
echo "Running frontend lint..."
if [ -d "web_frontend" ]; then
    cd web_frontend
    if [ -f "package.json" ]; then
        npm run lint || {
            echo "❌ Frontend lint failed!"
            exit 1
        }
    else
        echo "⚠️  package.json not found, skipping frontend lint"
    fi
    cd "$PROJECT_ROOT"
else
    echo "⚠️  web_frontend directory not found, skipping frontend lint"
fi

# Python 检查
echo "Running Python checks..."

# 查找虚拟环境
VENV_PATH=""
if [ -d "venv" ]; then
    VENV_PATH="venv"
elif [ -d ".venv" ]; then
    VENV_PATH=".venv"
fi

if [ -z "$VENV_PATH" ]; then
    echo "⚠️  Virtual environment not found, skipping Python checks"
    echo "   (Create one with: python3 -m venv venv)"
    exit 0
fi

# 使用虚拟环境执行
"$VENV_PATH/bin/flake8" backend/ core/ tests/ --exclude=venv,migrations,__pycache__,dist || {
    echo "❌ Flake8 failed!"
    exit 1
}

"$VENV_PATH/bin/black" backend/ core/ tests/ --exclude="venv|migrations|dist" --check || {
    echo "❌ Black check failed!"
    exit 1
}

echo "✅ All lint checks passed!"