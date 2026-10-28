#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)}"

if [[ -z "$PYTHON_BIN" ]]; then
    echo "No Python interpreter was found on PATH. Install Python 3.9+ or set PYTHON_BIN to its executable." >&2
    exit 1
fi

if ! "$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 9) else 1)'; then
    echo "Python 3.9+ is required. Found: $($PYTHON_BIN -V 2>&1)" >&2
    exit 1
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r "$SCRIPT_DIR/requirements.txt"

echo "Environment ready: $VENV_DIR"
echo "Run: $SCRIPT_DIR/launch.sh recording.edf --hypnogram stages.csv"
echo "VS Code interpreter: $VENV_DIR/bin/python"