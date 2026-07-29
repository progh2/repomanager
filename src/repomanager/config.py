"""Load configuration and secrets from environment / .env."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


def _find_dotenv() -> Path | None:
    """Search upward from cwd and package root for a .env file."""
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[2] / ".env",  # repo root when installed editable
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


def get_github_token() -> str:
    load_config()
    token = (os.getenv("GITHUB_TOKEN") or "").strip()
    if not token:
        raise ConfigError(
            "GITHUB_TOKEN is not set. Copy .env.example to .env and add your token."
        )
    if token.startswith("ghp_your_token") or token == "ghp_your_token_here":
        raise ConfigError(
            "GITHUB_TOKEN still has the placeholder value. Replace it with a real token."
        )
    return token
