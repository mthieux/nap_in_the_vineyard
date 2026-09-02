#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3.9}"

if [[ ! -x "$(command -v "$PYTHON_BIN" 2>/dev/null || true)" ]]; then
    echo "Python 3.9 is required but was not found. Install Python 3.9 or set PYTHON_BIN to its executable." >&2
    exit 1
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r "$SCRIPT_DIR/requirements-sleep-scoring.txt"

echo "Environment ready: $VENV_DIR"
echo "Run: $SCRIPT_DIR/launch_sleep_scoring.sh recording.edf --hypnogram stages.csv"
echo "VS Code interpreter: $VENV_DIR/bin/python"