"""Tests for GitHubClient with mocked PyGithub objects."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from github import GithubException

from repomanager.services.github_client import GitHubClient, GitHubClientError, RateLimitInfo


def _make_gh_repo(
    *,
    owner: str = "alice",
    name: str = "demo",
    private: bool = False,
    description: str = "desc",
    archived: bool = False,
) -> MagicMock:
    repo = MagicMock()
    repo.owner.login = owner
    repo.name = name
    repo.private = private
    repo.description = description
    repo.html_url = f"https://github.com/{owner}/{name}"
    repo.archived = archived
    repo.updated_at = datetime(2026, 1, 2, tzinfo=timezone.utc)
    return repo


@patch("repomanager.services.github_client.Github")
def test_list_repositories_maps_models(mock_github_cls: MagicMock) -> None:
    gh = mock_github_cls.return_value
    user = gh.get_user.return_value
    user.get_repos.return_value = [
        _make_gh_repo(owner="alice", name="one", private=True),
        _make_gh_repo(owner="org", name="two", description=""),
    ]

    client = GitHubClient("token")
    repos = client.list_repositories()

    assert len(repos) == 2
    assert repos[0].full_name == "alice/one"
    assert repos[0].visibility == "Private"
    assert repos[1].owner == "org"
    assert repos[1].short_description == "(설명 없음)"
    user.get_repos.assert_called_once()


@patch("repomanager.services.github_client.Github")
def test_verify_maps_401(mock_github_cls: MagicMock) -> None:
    gh = mock_github_cls.return_value
    gh.get_user.side_effect = GithubException(401, {"message": "Bad credentials"}, None)

    client = GitHubClient("bad")
    with pytest.raises(GitHubClientError) as exc_info:
        client.verify()
    assert exc_info.value.status == 401
    assert "Authentication failed" in str(exc_info.value)


@patch("repomanager.services.github_client.time.sleep", return_value=None)
@patch("repomanager.services.github_client.Github")
def test_archive_retries_on_rate_limit(
    mock_github_cls: MagicMock, _sleep: MagicMock
) -> None:
    gh = mock_github_cls.return_value
    repo = MagicMock()
    gh.get_repo.return_value = repo
    rate_exc = GithubException(403, {"message": "API rate limit exceeded"}, {"X-RateLimit-Reset": "1"})
    repo.edit.side_effect = [rate_exc, None]

    client = GitHubClient("token", max_retries=3)
    client.archive_repository("alice", "demo")

    assert repo.edit.call_count == 2
    repo.edit.assert_called_with(archived=True)


@patch("repomanager.services.github_client.Github")
def test_get_rate_limit(mock_github_cls: MagicMock) -> None:
    gh = mock_github_cls.return_value
    reset = datetime(2026, 7, 29, 12, 0, tzinfo=timezone.utc)
    core = SimpleNamespace(remaining=42, limit=5000, reset=reset)
    resources = SimpleNamespace(core=core)
    gh.get_rate_limit.return_value = SimpleNamespace(resources=resources)

    client = GitHubClient("token")
    info = client.get_rate_limit()

    assert isinstance(info, RateLimitInfo)
    assert info.remaining == 42
    assert info.limit == 5000
    assert "API 42/5000" in info.summary
