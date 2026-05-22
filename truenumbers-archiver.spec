# PyInstaller spec: builds tn-load and tn-archive with bundled dependencies.
# Run: pyinstaller --noconfirm --clean truenumbers-archiver.spec

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hiddenimports = (
    collect_submodules("truenumbers_python_lib")
    + collect_submodules("InquirerPy")
    + collect_submodules("prompt_toolkit")
    + ["helpers", "_venv_bootstrap"]
)

analysis_kwargs = {
    "pathex": ["src"],
    "binaries": [],
    "datas": [],
    "hiddenimports": hiddenimports,
    "hookspath": [],
    "hooksconfig": {},
    "runtime_hooks": [],
    "excludes": ["setuptools", "distutils"],
    "win_no_prefer_redirects": False,
    "win_private_assemblies": False,
    "cipher": block_cipher,
    "noarchive": False,
}

a_load = Analysis(["src/load.py"], **analysis_kwargs)
pyz_load = PYZ(a_load.pure, a_load.zipped_data, cipher=block_cipher)
exe_load = EXE(
    pyz_load,
    a_load.scripts,
    a_load.binaries,
    a_load.zipfiles,
    a_load.datas,
    [],
    name="tn-load",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

a_archive = Analysis(["src/archive.py"], **analysis_kwargs)
pyz_archive = PYZ(a_archive.pure, a_archive.zipped_data, cipher=block_cipher)
exe_archive = EXE(
    pyz_archive,
    a_archive.scripts,
    a_archive.binaries,
    a_archive.zipfiles,
    a_archive.datas,
    [],
    name="tn-archive",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
