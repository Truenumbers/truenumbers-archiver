#!/usr/bin/env bash
# Build tn-load and tn-archive executables with PyInstaller (deps bundled).
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
  echo "  .venv/Scripts/pip install -r requirements.txt -r requirements-build.txt" >&2
  exit 1
fi

"$PYTHON" -m pip install -r requirements.txt -r requirements-build.txt
"$PYTHON" -m PyInstaller --noconfirm --clean truenumbers-archiver.spec

echo ""
echo "Built:"
echo "  dist/tn-load$( [[ "$OSTYPE" == *msys* || "$OSTYPE" == *win32* ]] && echo .exe )"
echo "  dist/tn-archive$( [[ "$OSTYPE" == *msys* || "$OSTYPE" == *win32* ]] && echo .exe )"
