#!/usr/bin/env bash
# RepoManager launcher for macOS / Linux.
# Creates .venv on first run, installs dependencies, then starts the app.
set -euo pipefail
cd "$(dirname "$0")"

VENV_PY=".venv/bin/python"

find_python() {
    for cmd in python3 python; do
        if command -v "$cmd" >/dev/null 2>&1; then
            echo "$cmd"
            return 0
        fi
    done
    return 1
}

if [ ! -x "$VENV_PY" ]; then
    PY="$(find_python)" || {
        echo "[RepoManager] Python not found. Install Python 3.11+ first." >&2
        exit 1
    }
    echo "[RepoManager] Creating virtual environment..."
    "$PY" -m venv .venv
    echo "[RepoManager] Installing dependencies..."
    "$VENV_PY" -m pip install --upgrade pip
    "$VENV_PY" -m pip install -r requirements.txt
fi

if [ "${1:-}" = "--update" ]; then
    echo "[RepoManager] Updating dependencies..."
    "$VENV_PY" -m pip install --upgrade -r requirements.txt
fi

export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$VENV_PY" -m repomanager
