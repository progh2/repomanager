"""Tests for delete-forbidden error mapping."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from github import GithubException

from repomanager.services.github_client import GitHubClient, GitHubClientError


@patch.object(GitHubClient, "get_oauth_scopes", return_value=["repo", "read:org"])
@patch("repomanager.services.github_client.Github")
def test_delete_maps_missing_delete_repo(
    mock_github_cls: MagicMock, _scopes: MagicMock
) -> None:
    gh = mock_github_cls.return_value
    repo = MagicMock()
    gh.get_repo.return_value = repo
    repo.delete.side_effect = GithubException(403, {"message": "Must have admin rights"}, {})

    client = GitHubClient("token", max_retries=1)
    try:
        client.delete_repository("alice", "demo")
        raised = None
    except GitHubClientError as exc:
        raised = exc

    assert raised is not None
    assert raised.status == 403
    assert "delete_repo" in str(raised)
    assert "gh auth refresh" in str(raised)
