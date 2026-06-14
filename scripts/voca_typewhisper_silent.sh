#!/bin/zsh
set -euo pipefail

SCRIPT_DIR=${0:A:h}
PROJECT_DIR=${SCRIPT_DIR:h}
cd "$PROJECT_DIR"

mkdir -p logs

if [[ -n "${VOCA_PYTHON:-}" ]]; then
  PYTHON_BIN="$VOCA_PYTHON"
elif [[ -x "$PROJECT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
else
  PYTHON_BIN="$(command -v python3)"
fi

"$PYTHON_BIN" main.py >> logs/typewhisper-script.log 2>&1

# Script Runner uses stdout as replacement text. Keep it empty so Voca
# executes the command without inserting command output into the focused app.
printf ''
