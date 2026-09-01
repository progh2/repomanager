"""Build a standalone RepoManager executable for the current platform.

    python packaging/build.py

Artifacts land in ``dist/release/`` with names the in-app updater understands:

    RepoManager-<version>-windows-<arch>.exe   single executable
    RepoManager-<version>-macos-<arch>.dmg     drag-to-Applications disk image
    RepoManager-<version>-linux-<arch>         single executable
    SHA256SUMS.txt                             checksums for all of the above

Nothing a user downloads needs unzipping: double-click and go.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "packaging" / "repomanager.spec"
DIST = ROOT / "dist"
RELEASE = DIST / "release"
APP_NAME = "RepoManager"


def app_version() -> str:
    """Read __version__ without importing the package (PySide6 may be absent)."""
    text = (ROOT / "src" / "repomanager" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if match is None:
        raise SystemExit("Could not find __version__ in src/repomanager/__init__.py")
    return match.group(1)


def normalized_arch() -> str:
    value = (platform.machine() or "").lower()
    if value in {"amd64", "x86_64", "x64"}:
        return "x86_64"
    if value in {"arm64", "aarch64"}:
        return "arm64"
    return value or "unknown"


def platform_key() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def run(command: list[str], **kwargs) -> None:
    print("$", " ".join(command), flush=True)
    subprocess.run(command, check=True, cwd=str(ROOT), **kwargs)


def clean() -> None:
    for path in (DIST, ROOT / "build"):
        shutil.rmtree(path, ignore_errors=True)


def build_icons() -> None:
    sys.path.insert(0, str(ROOT / "packaging"))
    from make_icons import build_icons as _build  # noqa: PLC0415 — local helper

    _build(ROOT / "src" / "repomanager" / "ui" / "assets" / "icon.png", ROOT / "build" / "icons")


def run_pyinstaller(version: str) -> None:
    env = dict(os.environ, REPOMANAGER_VERSION=version)
    run(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", str(SPEC)],
        env=env,
    )


def package(version: str) -> list[Path]:
    """Move PyInstaller output into dist/release under its published name."""
    RELEASE.mkdir(parents=True, exist_ok=True)
    key, arch = platform_key(), normalized_arch()
    stem = f"{APP_NAME}-{version}-{key}-{arch}"

    if key == "windows":
        built = DIST / f"{APP_NAME}.exe"
        if not built.is_file():
            raise SystemExit(f"Expected {built} — PyInstaller produced nothing.")
        target = RELEASE / f"{stem}.exe"
        shutil.copy2(built, target)
        return [target]

    if key == "macos":
        bundle = DIST / f"{APP_NAME}.app"
        if not bundle.is_dir():
            raise SystemExit(f"Expected {bundle} — PyInstaller produced nothing.")
        # Ad-hoc sign so the bundle at least launches after the Gatekeeper prompt.
        subprocess.run(
            ["codesign", "--force", "--deep", "--sign", "-", str(bundle)],
            check=False,
            capture_output=True,
        )
        return [make_dmg(bundle, RELEASE / f"{stem}.dmg")]

    built = DIST / APP_NAME
    if not built.is_file():
        raise SystemExit(f"Expected {built} — PyInstaller produced nothing.")
    target = RELEASE / stem
    shutil.copy2(built, target)
    target.chmod(0o755)
    return [target]


def make_dmg(bundle: Path, target: Path) -> Path:
    """Wrap the .app in a disk image with an Applications shortcut to drag onto.

    A .dmg opens on double-click, so users never have to unzip anything.
    """
    target.unlink(missing_ok=True)
    staging = DIST / "dmg"
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    run(["cp", "-R", str(bundle), str(staging / bundle.name)])
    (staging / "Applications").symlink_to("/Applications")
    run(
        [
            "hdiutil",
            "create",
            "-volname",
            APP_NAME,
            "-srcfolder",
            str(staging),
            "-ov",
            "-format",
            "UDZO",
            str(target),
        ]
    )
    shutil.rmtree(staging, ignore_errors=True)
    return target


def write_checksums(paths: list[Path]) -> Path:
    lines = []
    for path in sorted(paths, key=lambda p: p.name):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.name}")
    target = RELEASE / "SHA256SUMS.txt"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-clean", action="store_true", help="keep previous build output")
    args = parser.parse_args()

    version = app_version()
    print(f"[build] {APP_NAME} {version} for {platform_key()}/{normalized_arch()}")

    if not args.no_clean:
        clean()
    build_icons()
    run_pyinstaller(version)
    artifacts = package(version)
    checksums = write_checksums(artifacts)

    print("\n[build] done:")
    for path in [*artifacts, checksums]:
        size = path.stat().st_size / (1024 * 1024)
        print(f"  {path.relative_to(ROOT)}  ({size:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
