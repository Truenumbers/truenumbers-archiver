#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
exec "$ROOT/.venv/Scripts/python.exe" "$ROOT/src/archive.py" "$@"
