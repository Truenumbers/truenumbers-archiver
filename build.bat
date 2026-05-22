@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo No .venv found. Create one first:
  echo   python -m venv .venv
  echo   .venv\Scripts\pip install -r requirements.txt -r requirements-build.txt
  exit /b 1
)

.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-build.txt
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean truenumbers-archiver.spec

echo.
echo Built:
echo   dist\tn-load.exe
echo   dist\tn-archive.exe
