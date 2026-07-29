"""GitHub API client wrapper."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, TypeVar

from github import Auth, Github, GithubException
from github.Repository import Repository as GhRepository

from repomanager.models.repository import Repository

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class RateLimitInfo:
    remaining: int
    limit: int
    reset_at: datetime | None

    @property
    def summary(self) -> str:
        reset = self.reset_at.strftime("%H:%M:%S") if self.reset_at else "?"
        return f"API {self.remaining}/{self.limit} (reset {reset})"


class GitHubClientError(Exception):
    """User-facing GitHub client error."""

    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class GitHubClient:
    def __init__(self, token: str, *, max_retries: int = 3) -> None:
        self._gh = Github(auth=Auth.Token(token), per_page=100)
        self._max_retries = max(1, max_retries)

    def verify(self) -> str:
        """Return the authenticated login, or raise GitHubClientError."""
        try:
            return self._call(lambda: self._gh.get_user().login)
        except GithubException as exc:
            raise self._map_exception(exc) from exc

    def get_rate_limit(self) -> RateLimitInfo:
        try:
            core = self._gh.get_rate_limit().resources.core
            reset = core.reset
            if reset is not None and reset.tzinfo is None:
                reset = reset.replace(tzinfo=timezone.utc)
            return RateLimitInfo(
                remaining=int(core.remaining),
                limit=int(core.limit),
                reset_at=reset if isinstance(reset, datetime) else None,
            )
        except GithubException as exc:
            raise self._map_exception(exc) from exc
        except AttributeError:
            # Older PyGithub shapes
            try:
                core = self._gh.get_rate_limit().core
                reset = core.reset
                if reset is not None and reset.tzinfo is None:
                    reset = reset.replace(tzinfo=timezone.utc)
                return RateLimitInfo(
                    remaining=int(core.remaining),
                    limit=int(core.limit),
                    reset_at=reset if isinstance(reset, datetime) else None,
                )
            except GithubException as exc:
                raise self._map_exception(exc) from exc

    def list_organizations(self) -> list[str]:
        """Return org logins the authenticated user belongs to."""
        try:
            user = self._gh.get_user()
            return [org.login for org in self._call(lambda: list(user.get_orgs()))]
        except GithubException as exc:
            raise self._map_exception(exc) from exc

    def list_repositories(
        self,
        *,
        affiliation: str = "owner,organization,collaborator",
    ) -> list[Repository]:
        """List repositories visible to the authenticated user."""
        try:
            user = self._gh.get_user()

            def _fetch() -> list[Repository]:
                repos = user.get_repos(
                    affiliation=affiliation,
                    sort="updated",
                    direction="desc",
                )
                return [self._to_model(repo) for repo in repos]

            return self._call(_fetch)
        except GithubException as exc:
            raise self._map_exception(exc) from exc

    def archive_repository(self, owner: str, name: str) -> None:
        try:
            def _archive() -> None:
                repo = self._gh.get_repo(f"{owner}/{name}")
                repo.edit(archived=True)

            self._call(_archive)
        except GithubException as exc:
            raise self._map_exception(exc) from exc

    def delete_repository(self, owner: str, name: str) -> None:
        try:
            def _delete() -> None:
                repo = self._gh.get_repo(f"{owner}/{name}")
                repo.delete()

            self._call(_delete)
        except GithubException as exc:
            raise self._map_exception(exc) from exc

    def _call(self, fn: Callable[[], T]) -> T:
        """Run ``fn`` with limited retries on rate-limit responses."""
        last_exc: GithubException | None = None
        for attempt in range(self._max_retries):
            try:
                return fn()
            except GithubException as exc:
                last_exc = exc
                if not self._is_rate_limited(exc) or attempt >= self._max_retries - 1:
                    raise
                wait_seconds = self._retry_wait_seconds(exc)
                time.sleep(wait_seconds)
        assert last_exc is not None
        raise last_exc

    def _retry_wait_seconds(self, exc: GithubException) -> float:
        headers = getattr(exc, "headers", None) or {}
        reset = headers.get("X-RateLimit-Reset") or headers.get("x-ratelimit-reset")
        if reset is not None:
            try:
                reset_ts = int(reset)
                wait = max(1, reset_ts - int(time.time()) + 1)
                return float(min(wait, 60))
            except (TypeError, ValueError):
                pass
        return 5.0 * (1 + getattr(exc, "status", 0) % 2)

    @staticmethod
    def _is_rate_limited(exc: GithubException) -> bool:
        if exc.status != 403:
            return False
        message = ""
        data = getattr(exc, "data", None)
        if isinstance(data, dict):
            message = str(data.get("message", "")).lower()
        else:
            message = str(exc).lower()
        return "rate limit" in message or "secondary rate" in message

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
            data = getattr(exc, "data", None)
            detail = ""
            if isinstance(data, dict):
                detail = str(data.get("message", ""))
            lowered = detail.lower()
            if "rate limit" in lowered or "secondary rate" in lowered:
                return GitHubClientError(
                    "GitHub API rate limit exceeded (403). Wait and try again.",
                    status=status,
                )
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
