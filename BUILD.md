# Building standalone executables

PyInstaller bundles `load.py` and `archive.py` (plus `helpers`, dependencies) into two one-file apps.

## Prerequisites

```bash
python -m venv .venv
# Windows
.venv\Scripts\pip install -r requirements.txt -r requirements-build.txt
# Linux / macOS
.venv/bin/pip install -r requirements.txt -r requirements-build.txt
```

## Build

```bash
# Windows
build.bat

# Git Bash / Linux / macOS
./build.sh
```

Output:

| Platform | Files |
|----------|--------|
| Windows | `dist/tn-load.exe`, `dist/tn-archive.exe` |
| Linux | `dist/tn-load`, `dist/tn-archive` |

**Build on the OS you deploy to.** A Windows build cannot run on Linux (build Linux binaries in CI or on a Linux host).

## Run (headless)

Pass CLI flags so InquirerPy prompts are skipped, for example:

```bash
./dist/tn-archive -a -e USER -p PASS -o ORG \
  --tn_rest_api https://example/truenumbers-rest-api \
  --archive_all_numberspaces

./dist/tn-load -a ... --load_all_numberspaces --load_from Truenumbers \
  -d /path/to/archived_numberspaces
```

## Troubleshooting

- **Import errors at runtime:** check `build/truenumbers-archiver/warn-truenumbers-archiver.txt` after a build.
- **Rebuild clean:** `pyinstaller --noconfirm --clean truenumbers-archiver.spec`
- **Dev runs (no bundle):** `python src/load.py` or `./load.sh` (uses `.venv`).
