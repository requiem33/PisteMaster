#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
PRE_COMMIT_HOOK="$GIT_HOOKS_DIR/pre-commit"
PRE_COMMIT_SCRIPT="$SCRIPT_DIR/pre-commit.sh"

if [ ! -d "$GIT_HOOKS_DIR" ]; then
    echo "Error: .git/hooks directory not found. Are you in a git repository?"
    exit 1
fi

if [ ! -f "$PRE_COMMIT_SCRIPT" ]; then
    echo "Error: pre-commit.sh script not found at $PRE_COMMIT_SCRIPT"
    exit 1
fi

cp "$PRE_COMMIT_SCRIPT" "$PRE_COMMIT_HOOK"
chmod +x "$PRE_COMMIT_HOOK"

echo "Pre-commit hook installed successfully!"
echo "The following lint checks will run before each commit:"
echo "  - Frontend: npm run lint"
echo "  - Python: flake8"
echo "  - Python: black --check"