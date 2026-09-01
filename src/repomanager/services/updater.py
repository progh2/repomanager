"""Check GitHub Releases for a newer build, download it, and install it in place.

The module is deliberately free of Qt and app-config imports so it can be unit
tested on its own; UI wiring lives in :mod:`repomanager.workers.update_worker`.
"""

from __future__ import annotations

import hashlib
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import requests

GITHUB_OWNER = "progh2"
GITHUB_REPO = "repomanager"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
CHECKSUM_ASSET = "SHA256SUMS.txt"
APP_NAME = "RepoManager"
USER_AGENT = "RepoManager-Updater"

ProgressCb = Callable[[int, int], None]  # downloaded bytes, total bytes (0 = unknown)
CancelCb = Callable[[], bool]


class UpdateError(Exception):
    """Any failure while checking, downloading, or installing an update."""


@dataclass(frozen=True, slots=True)
class UpdateInfo:
    version: str
    tag: str
    notes: str
    html_url: str
    asset_name: str
    asset_url: str
    asset_size: int
    sha256_url: str | None = None


# --- version comparison -------------------------------------------------


_NUMERIC_RE = re.compile(r"^\D*(\d+(?:\.\d+)*)(.*)$")


def parse_version(value: str) -> tuple[tuple[int, ...], int, str]:
    """Return a sortable key for a version string.

    ``0.4.0`` > ``0.4.0rc1`` > ``0.3.9``. Unparseable strings sort lowest.
    """
    match = _NUMERIC_RE.match((value or "").strip())
    if match is None:
        return ((), 0, "")
    numbers = tuple(int(part) for part in match.group(1).split("."))
    suffix = match.group(2).strip().lstrip("-_.").lower()
    # A bare release outranks any pre-release suffix of the same numbers.
    return (numbers, 0 if suffix else 1, suffix)


def is_newer(candidate: str, current: str) -> bool:
    return parse_version(candidate) > parse_version(current)


# --- platform / asset matching -----------------------------------------


def normalized_arch(machine: str | None = None) -> str:
    value = (machine or platform.machine() or "").lower()
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


def _asset_matches_platform(name: str, key: str) -> bool:
    lowered = name.lower()
    if key not in lowered:
        return False
    if key == "windows":
        return lowered.endswith(".exe")
    if key == "macos":
        return lowered.endswith((".dmg", ".zip"))
    return not lowered.endswith((".dmg", ".zip", ".exe", ".txt", ".sig", ".sha256"))


def select_asset(assets: list[dict], key: str | None = None, arch: str | None = None) -> dict | None:
    """Pick the release asset built for this platform, preferring an arch match."""
    key = key or platform_key()
    arch = arch or normalized_arch()
    candidates = [a for a in assets if _asset_matches_platform(str(a.get("name") or ""), key)]
    if not candidates:
        return None
    for asset in candidates:
        if arch in str(asset.get("name") or "").lower():
            return asset
    return candidates[0]


# --- checking -----------------------------------------------------------


def check_for_update(current_version: str, *, timeout: float = 15.0) -> UpdateInfo | None:
    """Return the latest release when it is newer than ``current_version``."""
    try:
        response = requests.get(
            RELEASES_API,
            headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT},
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise UpdateError(f"Could not reach GitHub: {exc}") from exc

    if response.status_code == 404:
        return None
    if response.status_code >= 400:
        raise UpdateError(f"GitHub returned HTTP {response.status_code} for the latest release.")

    try:
        data = response.json()
    except ValueError as exc:
        raise UpdateError("GitHub returned an unreadable release response.") from exc

    if data.get("draft"):
        return None
    tag = str(data.get("tag_name") or "").strip()
    latest = tag.lstrip("vV")
    if not latest or not is_newer(latest, current_version):
        return None

    assets = [a for a in (data.get("assets") or []) if isinstance(a, dict)]
    asset = select_asset(assets)
    checksum = next(
        (a for a in assets if str(a.get("name") or "").lower() == CHECKSUM_ASSET.lower()),
        None,
    )
    return UpdateInfo(
        version=latest,
        tag=tag,
        notes=str(data.get("body") or "").strip(),
        html_url=str(data.get("html_url") or RELEASES_PAGE),
        asset_name=str(asset.get("name")) if asset else "",
        asset_url=str(asset.get("browser_download_url")) if asset else "",
        asset_size=int(asset.get("size") or 0) if asset else 0,
        sha256_url=str(checksum.get("browser_download_url")) if checksum else None,
    )


# --- downloading --------------------------------------------------------


def _expected_sha256(info: UpdateInfo, *, timeout: float = 15.0) -> str | None:
    """Look up ``info.asset_name`` in the release's SHA256SUMS.txt, if published."""
    if not info.sha256_url:
        return None
    try:
        response = requests.get(
            info.sha256_url, headers={"User-Agent": USER_AGENT}, timeout=timeout
        )
        response.raise_for_status()
    except requests.RequestException:
        return None
    for line in response.text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[-1].lstrip("*") == info.asset_name:
            return parts[0].lower()
    return None


def download_asset(
    info: UpdateInfo,
    *,
    progress: ProgressCb | None = None,
    should_cancel: CancelCb | None = None,
    timeout: float = 30.0,
) -> Path:
    """Stream the asset into a temp directory, verifying its checksum when published."""
    if not info.asset_url:
        raise UpdateError("This release has no downloadable build for your platform.")

    staging = Path(tempfile.mkdtemp(prefix="repomanager-update-"))
    target = staging / info.asset_name
    digest = hashlib.sha256()
    downloaded = 0

    try:
        with requests.get(
            info.asset_url,
            headers={"User-Agent": USER_AGENT},
            stream=True,
            timeout=timeout,
        ) as response:
            response.raise_for_status()
            total = int(response.headers.get("Content-Length") or info.asset_size or 0)
            with target.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=256 * 1024):
                    if should_cancel is not None and should_cancel():
                        raise UpdateError("cancelled")
                    if not chunk:
                        continue
                    handle.write(chunk)
                    digest.update(chunk)
                    downloaded += len(chunk)
                    if progress is not None:
                        progress(downloaded, total)
    except requests.RequestException as exc:
        shutil.rmtree(staging, ignore_errors=True)
        raise UpdateError(f"Download failed: {exc}") from exc
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    expected = _expected_sha256(info)
    if expected and digest.hexdigest().lower() != expected:
        shutil.rmtree(staging, ignore_errors=True)
        raise UpdateError("Checksum mismatch — the download was corrupted or tampered with.")
    return target


# --- installing ---------------------------------------------------------


def is_frozen() -> bool:
    """True when running from a PyInstaller build rather than a source checkout."""
    return bool(getattr(sys, "frozen", False))


def install_target() -> Path:
    """The file or bundle that an update replaces."""
    executable = Path(sys.executable).resolve()
    if sys.platform == "darwin":
        for parent in executable.parents:
            if parent.suffix == ".app":
                return parent
    return executable


def can_self_update() -> bool:
    """True when this build can replace itself without admin rights."""
    if not is_frozen():
        return False
    target = install_target()
    return os.access(target.parent, os.W_OK)


def _run(command: list[str], failure: str, *, timeout: int = 300) -> None:
    completed = subprocess.run(
        command, check=False, capture_output=True, text=True, timeout=timeout
    )
    if completed.returncode != 0:
        raise UpdateError((completed.stderr or completed.stdout or failure).strip())


def _find_app(root: Path) -> Path:
    apps = sorted(root.glob("*.app")) or sorted(root.glob("*/*.app"))
    if not apps:
        raise UpdateError("The download did not contain a RepoManager.app bundle.")
    return apps[0]


def _extract_macos_app(archive: Path) -> Path:
    """Get RepoManager.app out of a .dmg (mount) or .zip (ditto) download."""
    unpacked = archive.parent / "unpacked"
    unpacked.mkdir(exist_ok=True)

    if archive.suffix.lower() == ".dmg":
        mount = archive.parent / "mnt"
        mount.mkdir(exist_ok=True)
        _run(
            ["hdiutil", "attach", "-nobrowse", "-readonly", "-mountpoint", str(mount), str(archive)],
            "Could not open the downloaded disk image.",
        )
        try:
            # Copy out of the image with ditto so symlinks and exec bits survive.
            _run(
                ["ditto", str(_find_app(mount)), str(unpacked / f"{APP_NAME}.app")],
                "Could not copy the app out of the disk image.",
            )
        finally:
            subprocess.run(
                ["hdiutil", "detach", str(mount), "-force"],
                check=False,
                capture_output=True,
                timeout=60,
            )
        return _find_app(unpacked)

    _run(
        ["ditto", "-x", "-k", str(archive), str(unpacked)],
        "Could not unpack the download.",
    )
    return _find_app(unpacked)


def _write_script(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def _windows_script(new_exe: Path, target: Path, pid: int) -> str:
    return (
        "@echo off\r\n"
        "setlocal\r\n"
        f'set "NEW={new_exe}"\r\n'
        f'set "TARGET={target}"\r\n'
        "set RETRY=0\r\n"
        ":wait\r\n"
        f'tasklist /fi "PID eq {pid}" 2>nul | find "{pid}" >nul || goto swap\r\n'
        "ping -n 2 127.0.0.1 >nul\r\n"
        "set /a RETRY+=1\r\n"
        "if %RETRY% LSS 60 goto wait\r\n"
        ":swap\r\n"
        "set RETRY=0\r\n"
        ":retry\r\n"
        'move /y "%NEW%" "%TARGET%" >nul 2>&1 && goto done\r\n'
        "ping -n 2 127.0.0.1 >nul\r\n"
        "set /a RETRY+=1\r\n"
        "if %RETRY% LSS 30 goto retry\r\n"
        "echo RepoManager could not be replaced. Install the new version manually:\r\n"
        'echo   %NEW%\r\n'
        "pause\r\n"
        "goto end\r\n"
        ":done\r\n"
        'start "" "%TARGET%"\r\n'
        ":end\r\n"
        'del "%~f0"\r\n'
    )


def _wait_for_pid_sh(pid: int) -> str:
    return (
        "i=0\n"
        "while [ $i -lt 120 ]; do\n"
        f"  kill -0 {pid} 2>/dev/null || break\n"
        "  sleep 0.5\n"
        "  i=$((i+1))\n"
        "done\n"
    )


def _macos_script(new_app: Path, target: Path, pid: int) -> str:
    backup = f"{target}.old"
    return (
        "#!/bin/sh\n"
        + _wait_for_pid_sh(pid)
        + f'rm -rf "{backup}"\n'
        f'mv "{target}" "{backup}" 2>/dev/null\n'
        f'if ! ditto "{new_app}" "{target}"; then\n'
        f'  rm -rf "{target}"\n'
        f'  mv "{backup}" "{target}" 2>/dev/null\n'
        f'  open -a Finder "{new_app}"\n'
        "  exit 1\n"
        "fi\n"
        f'rm -rf "{backup}"\n'
        f'xattr -dr com.apple.quarantine "{target}" 2>/dev/null\n'
        f'open "{target}"\n'
        'rm -f "$0"\n'
    )


def _linux_script(new_bin: Path, target: Path, pid: int) -> str:
    # Copy beside the target first: a same-directory rename is atomic and works
    # even if the old binary is still mapped.
    staged = f"{target}.new"
    return (
        "#!/bin/sh\n"
        + _wait_for_pid_sh(pid)
        + f'if ! cp -f "{new_bin}" "{staged}"; then\n'
        "  exit 1\n"
        "fi\n"
        f'chmod +x "{staged}"\n'
        f'mv -f "{staged}" "{target}" || exit 1\n'
        f'"{target}" &\n'
        'rm -f "$0"\n'
    )


def install(downloaded: Path, *, pid: int | None = None) -> None:
    """Hand the swap to a detached helper, then let the caller quit the app.

    The helper waits for this process to exit, replaces :func:`install_target`
    with the downloaded build, and relaunches RepoManager.
    """
    if not is_frozen():
        raise UpdateError(
            "Running from source — update with 'git pull' instead of the in-app installer."
        )
    downloaded = Path(downloaded).resolve()
    target = install_target()
    if not os.access(target.parent, os.W_OK):
        raise UpdateError(
            f"No write permission for {target.parent}. "
            "Move RepoManager somewhere writable or install the update manually."
        )

    pid = os.getpid() if pid is None else pid
    key = platform_key()
    if key == "windows":
        script = _write_script(
            downloaded.parent / "apply_update.cmd",
            _windows_script(downloaded, target, pid),
        )
        command = ["cmd", "/c", str(script)]
    elif key == "macos":
        new_app = _extract_macos_app(downloaded)
        script = _write_script(
            downloaded.parent / "apply_update.sh",
            _macos_script(new_app, target, pid),
        )
        command = ["/bin/sh", str(script)]
    else:
        script = _write_script(
            downloaded.parent / "apply_update.sh",
            _linux_script(downloaded, target, pid),
        )
        command = ["/bin/sh", str(script)]

    kwargs: dict = {"close_fds": True, "cwd": str(downloaded.parent)}
    if key == "windows":
        kwargs["creationflags"] = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(
            subprocess, "CREATE_NEW_PROCESS_GROUP", 0
        )
    else:
        kwargs["start_new_session"] = True
    try:
        subprocess.Popen(command, **kwargs)  # noqa: S603 — scripts we generated ourselves
    except OSError as exc:
        raise UpdateError(f"Could not start the updater helper: {exc}") from exc
