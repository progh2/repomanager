"""GitHub API client wrapper."""

from __future__ import annotations

from datetime import datetime, timezone

from github import Auth, Github, GithubException
from github.Repository import Repository as GhRepository

from repomanager.models.repository import Repository


class GitHubClientError(Exception):
    """User-facing GitHub client error."""

    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class GitHubClient:
    def __init__(self, token: str) -> None:
        self._gh = Github(auth=Auth.Token(token), per_page=100)

    def verify(self) -> str:
        """Return the authenticated login, or raise GitHubClientError."""
        try:
            user = self._gh.get_user()
            return user.login
        except GithubException as exc:
            raise self._map_exception(exc) from exc

    def list_repositories(self, *, affiliation: str = "owner") -> list[Repository]:
        """List repositories for the authenticated user."""
        try:
            user = self._gh.get_user()
            repos = user.get_repos(affiliation=affiliation, sort="updated", direction="desc")
            return [self._to_model(repo) for repo in repos]
        except GithubException as exc:
            raise self._map_exception(exc) from exc

    def archive_repository(self, owner: str, name: str) -> None:
        try:
            repo = self._gh.get_repo(f"{owner}/{name}")
            repo.edit(archived=True)
        except GithubException as exc:
            raise self._map_exception(exc) from exc

    def delete_repository(self, owner: str, name: str) -> None:
        try:
            repo = self._gh.get_repo(f"{owner}/{name}")
            repo.delete()
        except GithubException as exc:
            raise self._map_exception(exc) from exc

    @staticmethod
    def _to_model(repo: GhRepository) -> Repository:
        updated = repo.updated_at
        if updated is not None and updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        return Repository(
            owner=repo.owner.login,
            name=repo.name,
            private=bool(repo.private),
            description=repo.description or "",
            html_url=repo.html_url,
            archived=bool(repo.archived),
            updated_at=updated if isinstance(updated, datetime) else None,
        )

    @staticmethod
    def _map_exception(exc: GithubException) -> GitHubClientError:
        status = exc.status
        if status == 401:
            return GitHubClientError(
                "Authentication failed (401). Check that GITHUB_TOKEN is valid.",
                status=status,
            )
        if status == 403:
            return GitHubClientError(
                "Access denied (403). Token may lack required scopes "
                "(repo / delete_repo) or rate limit was exceeded.",
                status=status,
            )
        if status == 404:
            return GitHubClientError(
                "Repository not found (404), or token cannot see it.",
                status=status,
            )
        message = getattr(exc, "data", None)
        if isinstance(message, dict) and message.get("message"):
            detail = str(message["message"])
        else:
            detail = str(exc)
        return GitHubClientError(f"GitHub API error ({status}): {detail}", status=status)
