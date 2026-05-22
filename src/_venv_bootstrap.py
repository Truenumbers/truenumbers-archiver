"""Re-run the script with the project .venv when dependencies are missing."""
import os
import subprocess
import sys
from pathlib import Path

_REEXEC_FLAG = "TN_ARCHIVER_VENV_REEXEC"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _venv_python(root: Path) -> Path | None:
    if sys.platform == "win32":
        candidate = root / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = root / ".venv" / "bin" / "python"
    return candidate if candidate.is_file() else None


def ensure_project_venv() -> None:
    if os.environ.get(_REEXEC_FLAG):
        return

    try:
        import truenumbers_python_lib  # noqa: F401
        return
    except ImportError:
        pass

    root = _project_root()
    venv_python = _venv_python(root)
    if venv_python is None:
        print(
            "Missing dependencies. Create a venv and install requirements:\n"
            f"  cd {root}\n"
            "  python -m venv .venv\n"
            "  .venv\\Scripts\\pip install -r requirements.txt   (Windows)\n"
            "  .venv/bin/pip install -r requirements.txt          (macOS/Linux)",
            file=sys.stderr,
        )
        sys.exit(1)

    if Path(sys.executable).resolve() == venv_python.resolve():
        print(
            "Missing truenumbers_python_lib in the project .venv. Run:\n"
            f"  {venv_python} -m pip install -r {root / 'requirements.txt'}",
            file=sys.stderr,
        )
        sys.exit(1)

    env = {**os.environ, _REEXEC_FLAG: "1"}
    raise SystemExit(subprocess.call([str(venv_python), *sys.argv], env=env))


ensure_project_venv()
