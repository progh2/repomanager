# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec shared by all platforms.

Windows and Linux produce a single self-contained executable; macOS produces a
``RepoManager.app`` bundle (a onefile binary cannot be a proper .app).
Run it through ``python packaging/build.py`` rather than directly.
"""

import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

ROOT = Path(SPECPATH).resolve().parent  # noqa: F821 — injected by PyInstaller
SRC = ROOT / "src"
UI = SRC / "repomanager" / "ui"
ICON_DIR = ROOT / "build" / "icons"

APP_NAME = "RepoManager"
IS_MACOS = sys.platform == "darwin"
IS_WINDOWS = sys.platform.startswith("win")


def _icon():
    candidate = ICON_DIR / ("repomanager.icns" if IS_MACOS else "repomanager.ico")
    return str(candidate) if IS_WINDOWS or IS_MACOS else None


datas = [
    (str(UI / "styles.qss"), "repomanager/ui"),
    (str(UI / "styles_dark.qss"), "repomanager/ui"),
    (str(UI / "assets" / "icon.png"), "repomanager/ui/assets"),
]

# keyring picks its backend at runtime, so the modules are never imported statically.
hiddenimports = collect_submodules("keyring.backends") + [
    "keyring.backends.chainer",
    "keyring.backends.fail",
]

# PySide6/__init__.py resolves `<PySide6 parent>/shiboken6` at import time and raises
#   ImportError: ...\shiboken6 does not exist
# if that directory is absent from the bundle. Relying on PySide6's hook to drag
# shiboken6 in is not dependable, so collect it explicitly.
shiboken_datas, shiboken_binaries, shiboken_hidden = collect_all("shiboken6")
datas += shiboken_datas
binaries = list(shiboken_binaries)
hiddenimports += [*shiboken_hidden, "shiboken6"]

# Only non-Qt extras are excluded. PyInstaller already collects just the Qt modules
# this app imports, and hand-excluding PySide6 submodules risks breaking that graph.
excludes = [
    "tkinter",
    "test",
    "pydoc_data",
]

if IS_MACOS:
    # cryptography's _rust extension links against libssl, and the libssl that
    # gets bundled on the Intel runner is older than the symbols it needs:
    #   Symbol not found: _SSL_get0_group_name ... Expected in: libssl.3.dylib
    # Nothing here uses cryptography. It arrives via PyGithub -> pyjwt[crypto],
    # which is only needed for GitHub App (JWT) auth; this app authenticates with
    # personal access tokens and OAuth device flow. PyJWT guards the import with
    # `except ModuleNotFoundError` and degrades to has_crypto = False.
    #
    # macOS only: on Linux the SecretService keyring backend needs cryptography
    # (via secretstorage), and dropping it there would silently downgrade token
    # storage to plaintext QSettings.
    excludes += ["cryptography"]

a = Analysis(  # noqa: F821
    [str(SRC / "repomanager" / "__main__.py")],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)
pyz = PYZ(a.pure)  # noqa: F821

if IS_MACOS:
    # onedir + BUNDLE: macOS needs a real .app directory layout.
    exe = EXE(  # noqa: F821
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=_icon(),
    )
    coll = COLLECT(  # noqa: F821
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name=APP_NAME,
    )
    app = BUNDLE(  # noqa: F821
        coll,
        name=f"{APP_NAME}.app",
        icon=_icon(),
        bundle_identifier="io.github.progh2.repomanager",
        info_plist={
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": APP_NAME,
            "CFBundleShortVersionString": os.environ.get("REPOMANAGER_VERSION", "0.0.0"),
            "CFBundleVersion": os.environ.get("REPOMANAGER_VERSION", "0.0.0"),
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
        },
    )
else:
    exe = EXE(  # noqa: F821
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=_icon(),
    )
