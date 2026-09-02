#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "The project environment is missing. Run $SCRIPT_DIR/setup_sleep_scoring.sh first." >&2
    exit 1
fi

exec "$VENV_PYTHON" "$SCRIPT_DIR/run_sleep_sco.py" "$@"