"""Load configuration and secrets from environment, settings, and optional CLI."""

from __future__ import annotations

import os
import subprocess
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


def get_saved_token() -> str:
    return str(app_settings().value(KEY_TOKEN, "") or "").strip()


def set_saved_token(token: str) -> None:
    settings = app_settings()
    token = token.strip()
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
    return bool(app_settings().value(KEY_USE_GH_CLI, False))


def set_use_gh_cli(enabled: bool) -> None:
    settings = app_settings()
    settings.setValue(KEY_USE_GH_CLI, enabled)
    settings.sync()


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
    load_config()

    env_token = (os.getenv("GITHUB_TOKEN") or "").strip()
    if env_token and not _is_placeholder(env_token):
        return env_token
    if env_token and _is_placeholder(env_token):
        raise ConfigError(
            "GITHUB_TOKEN still has the placeholder value. "
            "Open Settings or replace it in .env."
        )

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

    raise ConfigError(
        "GitHub 토큰이 없습니다. 파일 → 설정에서 PAT를 넣거나, "
        "GitHub CLI에서 가져오거나, 웹 로그인을 사용하세요."
    )


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

