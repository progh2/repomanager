"""Load configuration and secrets from environment, settings, and optional CLI."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from dotenv import load_dotenv
from PySide6.QtCore import QSettings


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


SETTINGS_ORG = "RepoManager"
SETTINGS_APP = "RepoManager"
KEY_TOKEN = "github/token"
KEY_CLIENT_ID = "github/oauth_client_id"
KEY_USE_GH_CLI = "github/use_gh_cli"
KEY_AUTO_UPDATE = "updates/auto_check"
KEY_SKIPPED_VERSION = "updates/skipped_version"
KEY_LAST_UPDATE_CHECK = "updates/last_check"

AUTO_UPDATE_INTERVAL_HOURS = 24

KEYRING_SERVICE = "RepoManager"
KEYRING_USER = "github_token"

_keyring_ok: bool | None = None


def _keyring_available() -> bool:
    """Probe the OS credential store once and cache the result."""
    global _keyring_ok
    if _keyring_ok is not None:
        return _keyring_ok
    try:
        import keyring

        keyring.get_password(KEYRING_SERVICE, "__probe__")
        _keyring_ok = True
    except Exception:  # noqa: BLE001 — any backend failure means "not usable"
        _keyring_ok = False
    return _keyring_ok


def token_storage_is_secure() -> bool:
    """True when tokens are kept in the OS credential store instead of QSettings."""
    return _keyring_available()


def _find_dotenv() -> Path | None:
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[2] / ".env",
        Path(__file__).resolve().parents[3] / ".env",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def load_config() -> None:
    env_path = _find_dotenv()
    if env_path is not None:
        load_dotenv(env_path)
    else:
        load_dotenv()


def app_settings() -> QSettings:
    return QSettings(SETTINGS_ORG, SETTINGS_APP)


def _get_qsettings_token() -> str:
    return str(app_settings().value(KEY_TOKEN, "") or "").strip()


def _remove_qsettings_token() -> None:
    settings = app_settings()
    settings.remove(KEY_TOKEN)
    settings.sync()


def get_saved_token() -> str:
    if _keyring_available():
        import keyring

        try:
            token = (keyring.get_password(KEYRING_SERVICE, KEYRING_USER) or "").strip()
        except Exception:  # noqa: BLE001
            token = ""
        if token:
            return token
        # Migrate a token previously stored in QSettings (plaintext) to keyring.
        legacy = _get_qsettings_token()
        if legacy:
            try:
                keyring.set_password(KEYRING_SERVICE, KEYRING_USER, legacy)
                _remove_qsettings_token()
            except Exception:  # noqa: BLE001
                pass
            return legacy
        return ""
    return _get_qsettings_token()


def set_saved_token(token: str) -> None:
    token = token.strip()
    if _keyring_available():
        import keyring

        try:
            if token:
                keyring.set_password(KEYRING_SERVICE, KEYRING_USER, token)
            else:
                try:
                    keyring.delete_password(KEYRING_SERVICE, KEYRING_USER)
                except Exception:  # noqa: BLE001 — nothing stored yet
                    pass
            _remove_qsettings_token()
            return
        except Exception:  # noqa: BLE001 — fall back to QSettings below
            pass
    settings = app_settings()
    if token:
        settings.setValue(KEY_TOKEN, token)
    else:
        settings.remove(KEY_TOKEN)
    settings.sync()


def clear_saved_token() -> None:
    set_saved_token("")


def get_oauth_client_id() -> str:
    load_config()
    env_id = (os.getenv("GITHUB_OAUTH_CLIENT_ID") or "").strip()
    if env_id:
        return env_id
    return str(app_settings().value(KEY_CLIENT_ID, "") or "").strip()


def set_oauth_client_id(client_id: str) -> None:
    settings = app_settings()
    client_id = client_id.strip()
    if client_id:
        settings.setValue(KEY_CLIENT_ID, client_id)
    else:
        settings.remove(KEY_CLIENT_ID)
    settings.sync()


def get_use_gh_cli() -> bool:
    value = app_settings().value(KEY_USE_GH_CLI, False)
    if isinstance(value, str):
        return value.lower() in {"true", "1", "yes"}
    return bool(value)


def set_use_gh_cli(enabled: bool) -> None:
    settings = app_settings()
    settings.setValue(KEY_USE_GH_CLI, enabled)
    settings.sync()


def get_auto_update_check() -> bool:
    """Whether to look for a new release shortly after launch."""
    value = app_settings().value(KEY_AUTO_UPDATE, True)
    if isinstance(value, str):
        return value.lower() in {"true", "1", "yes"}
    return bool(value)


def set_auto_update_check(enabled: bool) -> None:
    settings = app_settings()
    settings.setValue(KEY_AUTO_UPDATE, bool(enabled))
    settings.sync()


def get_skipped_update_version() -> str:
    return str(app_settings().value(KEY_SKIPPED_VERSION, "") or "").strip()


def set_skipped_update_version(version: str) -> None:
    settings = app_settings()
    version = version.strip()
    if version:
        settings.setValue(KEY_SKIPPED_VERSION, version)
    else:
        settings.remove(KEY_SKIPPED_VERSION)
    settings.sync()


def mark_update_checked(now: float | None = None) -> None:
    settings = app_settings()
    settings.setValue(KEY_LAST_UPDATE_CHECK, time.time() if now is None else now)
    settings.sync()


def auto_update_check_due(now: float | None = None) -> bool:
    """True when the automatic check is enabled and last ran over a day ago."""
    if not get_auto_update_check():
        return False
    try:
        last = float(app_settings().value(KEY_LAST_UPDATE_CHECK, 0.0) or 0.0)
    except (TypeError, ValueError):
        last = 0.0
    now = time.time() if now is None else now
    return (now - last) >= AUTO_UPDATE_INTERVAL_HOURS * 3600


def try_gh_cli_token() -> str | None:
    """Return token from ``gh auth token`` if available."""
    try:
        completed = subprocess.run(
            ["gh", "auth", "token"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    if completed.returncode != 0:
        return None
    token = (completed.stdout or "").strip()
    return token or None


def _is_placeholder(token: str) -> bool:
    return token.startswith("ghp_your_token") or token == "ghp_your_token_here"


def get_github_token() -> str:
    """Resolve token: env → optional gh CLI → saved settings."""
    from repomanager.i18n import tr

    load_config()

    env_token = (os.getenv("GITHUB_TOKEN") or "").strip()
    if env_token and not _is_placeholder(env_token):
        return env_token
    if env_token and _is_placeholder(env_token):
        raise ConfigError(tr("config.placeholder_token"))

    if get_use_gh_cli():
        gh_token = try_gh_cli_token()
        if gh_token:
            return gh_token

    saved = get_saved_token()
    if saved:
        return saved

    # Last resort: gh CLI even if checkbox off (convenient when already logged in)
    gh_token = try_gh_cli_token()
    if gh_token:
        return gh_token

    raise ConfigError(tr("config.no_token"))


def token_source_label() -> str:
    """Best-effort label for UI status (does not validate the token)."""
    from repomanager.i18n import tr

    load_config()
    env_token = (os.getenv("GITHUB_TOKEN") or "").strip()
    if env_token and not _is_placeholder(env_token):
        return tr("token.source.env")
    if get_use_gh_cli() and try_gh_cli_token():
        return tr("token.source.gh")
    if get_saved_token():
        return tr("token.source.settings")
    if try_gh_cli_token():
        return tr("token.source.gh")
    return tr("token.source.none")
