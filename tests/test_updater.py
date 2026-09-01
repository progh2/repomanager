"""Tests for release checking, asset selection, and update staging."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from repomanager.services.updater import (
    UpdateError,
    UpdateInfo,
    check_for_update,
    download_asset,
    install,
    install_target,
    is_newer,
    normalized_arch,
    parse_version,
    select_asset,
)


def test_parse_version_orders_releases_above_prereleases() -> None:
    assert parse_version("0.4.0") > parse_version("0.4.0rc1")
    assert parse_version("0.4.0rc1") > parse_version("0.3.9")
    assert parse_version("nonsense") < parse_version("0.0.1")


@pytest.mark.parametrize(
    ("candidate", "current", "expected"),
    [
        ("0.4.0", "0.3.0", True),
        ("0.10.0", "0.9.9", True),
        ("0.3.0", "0.3.0", False),
        ("0.2.9", "0.3.0", False),
        ("1.0.0", "0.99.99", True),
    ],
)
def test_is_newer(candidate: str, current: str, expected: bool) -> None:
    assert is_newer(candidate, current) is expected


def test_normalized_arch() -> None:
    assert normalized_arch("AMD64") == "x86_64"
    assert normalized_arch("aarch64") == "arm64"


RELEASE_ASSETS = [
    {"name": "RepoManager-0.4.0-linux-arm64"},
    {"name": "RepoManager-0.4.0-linux-x86_64"},
    {"name": "RepoManager-0.4.0-windows-x86_64.exe"},
    {"name": "RepoManager-0.4.0-macos-arm64.dmg"},
    {"name": "RepoManager-0.4.0-macos-x86_64.dmg"},
    {"name": "SHA256SUMS.txt"},
]


@pytest.mark.parametrize(
    ("key", "arch", "expected"),
    [
        ("linux", "x86_64", "RepoManager-0.4.0-linux-x86_64"),
        ("linux", "arm64", "RepoManager-0.4.0-linux-arm64"),
        ("windows", "x86_64", "RepoManager-0.4.0-windows-x86_64.exe"),
        ("macos", "arm64", "RepoManager-0.4.0-macos-arm64.dmg"),
        ("macos", "x86_64", "RepoManager-0.4.0-macos-x86_64.dmg"),
    ],
)
def test_select_asset_matches_platform_and_arch(key: str, arch: str, expected: str) -> None:
    assert select_asset(RELEASE_ASSETS, key, arch)["name"] == expected


def test_select_asset_accepts_legacy_macos_zip() -> None:
    """Releases published before the .dmg switch must still be installable."""
    assets = [{"name": "RepoManager-0.3.0-macos-arm64.zip"}]
    assert select_asset(assets, "macos", "arm64")["name"].endswith(".zip")


def test_select_asset_never_picks_the_checksum_file() -> None:
    assert select_asset([{"name": "SHA256SUMS.txt"}], "linux", "x86_64") is None


def test_select_asset_returns_none_without_platform_build() -> None:
    assets = [{"name": "RepoManager-0.4.0-windows-x86_64.exe"}]
    assert select_asset(assets, "macos", "arm64") is None


def _release_payload(tag: str = "v0.4.0") -> dict:
    return {
        "tag_name": tag,
        "body": "notes",
        "html_url": "https://example.invalid/release",
        "draft": False,
        "assets": [
            {
                "name": "RepoManager-0.4.0-linux-x86_64",
                "browser_download_url": "https://example.invalid/bin",
                "size": 1234,
            },
            {
                "name": "SHA256SUMS.txt",
                "browser_download_url": "https://example.invalid/sums",
                "size": 90,
            },
        ],
    }


@patch("repomanager.services.updater.platform_key", return_value="linux")
@patch("repomanager.services.updater.normalized_arch", return_value="x86_64")
@patch("repomanager.services.updater.requests.get")
def test_check_for_update_returns_newer_release(
    mock_get: MagicMock, _arch: MagicMock, _key: MagicMock
) -> None:
    mock_get.return_value = MagicMock(status_code=200, json=lambda: _release_payload())

    info = check_for_update("0.3.0")

    assert info is not None
    assert info.version == "0.4.0"
    assert info.asset_name == "RepoManager-0.4.0-linux-x86_64"
    assert info.sha256_url == "https://example.invalid/sums"


@patch("repomanager.services.updater.requests.get")
def test_check_for_update_ignores_same_version(mock_get: MagicMock) -> None:
    mock_get.return_value = MagicMock(status_code=200, json=lambda: _release_payload())
    assert check_for_update("0.4.0") is None


@patch("repomanager.services.updater.requests.get")
def test_check_for_update_ignores_drafts(mock_get: MagicMock) -> None:
    payload = _release_payload() | {"draft": True}
    mock_get.return_value = MagicMock(status_code=200, json=lambda: payload)
    assert check_for_update("0.1.0") is None


@patch("repomanager.services.updater.requests.get")
def test_check_for_update_raises_on_http_error(mock_get: MagicMock) -> None:
    mock_get.return_value = MagicMock(status_code=500, json=dict)
    with pytest.raises(UpdateError):
        check_for_update("0.1.0")


def _download_response(payload: bytes) -> MagicMock:
    response = MagicMock()
    response.headers = {"Content-Length": str(len(payload))}
    response.iter_content.return_value = [payload]
    response.__enter__ = lambda self: self
    response.__exit__ = lambda self, *args: False
    return response


@patch("repomanager.services.updater._expected_sha256", return_value=None)
@patch("repomanager.services.updater.requests.get")
def test_download_asset_writes_file_and_reports_progress(
    mock_get: MagicMock, _sha: MagicMock
) -> None:
    payload = b"binary-payload"
    mock_get.return_value = _download_response(payload)
    info = UpdateInfo(
        version="0.4.0",
        tag="v0.4.0",
        notes="",
        html_url="",
        asset_name="RepoManager-0.4.0-linux-x86_64",
        asset_url="https://example.invalid/bin",
        asset_size=len(payload),
    )
    seen: list[tuple[int, int]] = []

    path = download_asset(info, progress=lambda done, total: seen.append((done, total)))

    assert path.read_bytes() == payload
    assert seen == [(len(payload), len(payload))]


@patch("repomanager.services.updater.requests.get")
def test_download_asset_rejects_checksum_mismatch(mock_get: MagicMock) -> None:
    payload = b"binary-payload"
    mock_get.return_value = _download_response(payload)
    info = UpdateInfo(
        version="0.4.0",
        tag="v0.4.0",
        notes="",
        html_url="",
        asset_name="RepoManager-0.4.0-linux-x86_64",
        asset_url="https://example.invalid/bin",
        asset_size=len(payload),
        sha256_url="https://example.invalid/sums",
    )
    with patch(
        "repomanager.services.updater._expected_sha256",
        return_value=hashlib.sha256(b"different").hexdigest(),
    ):
        with pytest.raises(UpdateError, match="Checksum mismatch"):
            download_asset(info)


def test_install_refuses_when_running_from_source(tmp_path: Path) -> None:
    artifact = tmp_path / "RepoManager-0.4.0-linux-x86_64"
    artifact.write_bytes(b"x")
    with pytest.raises(UpdateError, match="Running from source"):
        install(artifact)


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS bundle layout")
def test_install_target_is_the_app_bundle() -> None:
    with patch.object(sys, "executable", "/Applications/RepoManager.app/Contents/MacOS/RepoManager"):
        assert install_target() == Path("/Applications/RepoManager.app")


@patch("repomanager.services.updater.is_frozen", return_value=True)
@patch("repomanager.services.updater.subprocess.Popen")
def test_install_stages_helper_script(
    mock_popen: MagicMock, _frozen: MagicMock, tmp_path: Path
) -> None:
    artifact = tmp_path / "RepoManager-0.4.0-linux-x86_64"
    artifact.write_bytes(b"new build")
    target = tmp_path / "installed" / "RepoManager"
    target.parent.mkdir()
    target.write_bytes(b"old build")

    with patch("repomanager.services.updater.install_target", return_value=target):
        with patch("repomanager.services.updater.platform_key", return_value="linux"):
            install(artifact, pid=4242)

    script = tmp_path / "apply_update.sh"
    body = script.read_text(encoding="utf-8")
    assert "kill -0 4242" in body
    assert str(target) in body
    assert mock_popen.call_args.args[0] == ["/bin/sh", str(script)]


@patch("repomanager.services.updater.is_frozen", return_value=True)
def test_install_reports_unwritable_location(_frozen: MagicMock, tmp_path: Path) -> None:
    """An install directory the user cannot write to must fail before staging.

    os.access is patched rather than chmod'ing a directory: on Windows chmod
    does not make a directory read-only, so the filesystem trick is POSIX-only.
    """
    artifact = tmp_path / "RepoManager-0.4.0-linux-x86_64"
    artifact.write_bytes(b"new build")
    target = tmp_path / "locked" / "RepoManager"
    target.parent.mkdir()
    target.write_bytes(b"old")

    with patch("repomanager.services.updater.install_target", return_value=target):
        with patch("repomanager.services.updater.os.access", return_value=False):
            with pytest.raises(UpdateError, match="No write permission"):
                install(artifact)
