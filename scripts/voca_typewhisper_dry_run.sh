#!/bin/zsh
set -euo pipefail

SCRIPT_DIR=${0:A:h}
PROJECT_DIR=${SCRIPT_DIR:h}
cd "$PROJECT_DIR"

if [[ -n "${VOCA_PYTHON:-}" ]]; then
  PYTHON_BIN="$VOCA_PYTHON"
elif [[ -x "$PROJECT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
else
  PYTHON_BIN="$(command -v python3)"
fi

exec "$PYTHON_BIN" main.py --dry-run "$@"
