#!/usr/bin/env bash
# Run archive.py with the project .venv (Windows or Linux/macOS).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ -f "$ROOT/.venv/Scripts/python.exe" ]]; then
  PYTHON="$ROOT/.venv/Scripts/python.exe"
elif [[ -f "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  echo "No .venv found. Create one first:" >&2
  echo "  python -m venv .venv" >&2
  echo "  .venv\\Scripts\\pip install -r requirements.txt   (Windows)" >&2
  echo "  .venv/bin/pip install -r requirements.txt          (Linux/macOS)" >&2
  exit 1
fi

exec "$PYTHON" "$ROOT/src/archive.py" "$@"
