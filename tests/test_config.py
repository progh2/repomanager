"""Tests for token resolution helpers."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from repomanager import config


def test_get_github_token_prefers_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_env_token_value")
    with patch.object(config, "get_saved_token", return_value="saved"):
        assert config.get_github_token() == "ghp_env_token_value"


def test_get_github_token_uses_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with (
        patch.object(config, "load_config"),
        patch.object(config, "get_use_gh_cli", return_value=False),
        patch.object(config, "try_gh_cli_token", return_value=None),
        patch.object(config, "get_saved_token", return_value="ghp_saved"),
    ):
        assert config.get_github_token() == "ghp_saved"


def test_get_github_token_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with (
        patch.object(config, "load_config"),
        patch.object(config, "get_use_gh_cli", return_value=False),
        patch.object(config, "try_gh_cli_token", return_value=None),
        patch.object(config, "get_saved_token", return_value=""),
    ):
        with pytest.raises(config.ConfigError):
            config.get_github_token()


def test_oauth_client_id_falls_back_to_the_built_in_app() -> None:
    """Users should not have to register an OAuth App just to sign in."""
    with patch("repomanager.config.get_custom_oauth_client_id", return_value=""):
        assert config.get_oauth_client_id() == config.DEFAULT_OAUTH_CLIENT_ID


def test_custom_oauth_client_id_wins() -> None:
    with patch("repomanager.config.get_custom_oauth_client_id", return_value="Ov23custom"):
        assert config.get_oauth_client_id() == "Ov23custom"
