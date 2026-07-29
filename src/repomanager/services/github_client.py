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

    def unarchive_repository(self, owner: str, name: str) -> None:
        try:
            def _unarchive() -> None:
                repo = self._gh.get_repo(f"{owner}/{name}")
                repo.edit(archived=False)

            self._call(_unarchive)
        except GithubException as exc:
            raise self._map_exception(exc) from exc

    def delete_repository(self, owner: str, name: str) -> None:
        try:
            def _delete() -> None:
                repo = self._gh.get_repo(f"{owner}/{name}")
                repo.delete()

            self._call(_delete)
        except GithubException as exc:
            if exc.status == 403:
                raise self._map_delete_forbidden(exc) from exc
            raise self._map_exception(exc) from exc

    def update_description(self, owner: str, name: str, description: str) -> Repository:
        try:
            def _edit() -> Repository:
                repo = self._gh.get_repo(f"{owner}/{name}")
                repo.edit(description=description)
                return self._to_model(repo)

            return self._call(_edit)
        except GithubException as exc:
            raise self._map_exception(exc) from exc

    def set_private(self, owner: str, name: str, private: bool) -> Repository:
        try:
            def _edit() -> Repository:
                repo = self._gh.get_repo(f"{owner}/{name}")
                repo.edit(private=private)
                return self._to_model(repo)

            return self._call(_edit)
        except GithubException as exc:
            raise self._map_exception(exc) from exc

    def get_readme_excerpt(self, owner: str, name: str, *, max_chars: int = 4000) -> str:
        try:
            def _read() -> str:
                repo = self._gh.get_repo(f"{owner}/{name}")
                try:
                    content = repo.get_readme()
                except GithubException as exc:
                    if exc.status == 404:
                        return ""
                    raise
                text = content.decoded_content.decode("utf-8", errors="replace")
                return text[:max_chars]

            return self._call(_read)
        except GithubException as exc:
            raise self._map_exception(exc) from exc

    def get_oauth_scopes(self) -> list[str] | None:
        """Return classic OAuth scopes, or None for fine-grained tokens."""
        try:
            headers, _data = self._gh._Github__requester.requestJsonAndCheck(  # noqa: SLF001
                "GET", "/user"
            )
        except GithubException as exc:
            raise self._map_exception(exc) from exc
        raw = headers.get("x-oauth-scopes") or headers.get("X-OAuth-Scopes")
        if raw is None or raw == "":
            return None
        return [part.strip() for part in str(raw).split(",") if part.strip()]

    def _map_delete_forbidden(self, exc: GithubException) -> GitHubClientError:
        scopes = None
        try:
            scopes = self.get_oauth_scopes()
        except GitHubClientError:
            scopes = None
        detail = ""
        data = getattr(exc, "data", None)
        if isinstance(data, dict):
            detail = str(data.get("message", ""))
        if scopes is not None and "delete_repo" not in scopes:
            return GitHubClientError(
                "Access denied (403): token lacks delete_repo scope "
                f"(current: {', '.join(scopes) or 'none'}). "
                "Run: gh auth refresh -h github.com -s delete_repo "
                "or create a classic PAT with delete_repo, then update Settings.",
                status=403,
            )
        if scopes is None:
            return GitHubClientError(
                "Access denied (403) deleting repository. "
                "Fine-grained PATs need Administration: Read and write. "
                "Classic/OAuth tokens need the delete_repo scope. "
                f"GitHub said: {detail or 'forbidden'}",
                status=403,
            )
        return self._map_exception(exc)

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
    def _normalize_dt(value: object) -> datetime | None:
        if not isinstance(value, datetime):
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    @staticmethod
    def _guess_pages_url(owner: str, name: str, has_pages: bool) -> str:
        if not has_pages:
            return ""
        if name.lower() == f"{owner.lower()}.github.io":
            return f"https://{owner}.github.io/"
        return f"https://{owner}.github.io/{name}/"

    @classmethod
    def _to_model(cls, repo: GhRepository) -> Repository:
        created = cls._normalize_dt(repo.created_at)
        updated = cls._normalize_dt(repo.updated_at)
        has_pages = bool(getattr(repo, "has_pages", False))
        pages_url = cls._guess_pages_url(repo.owner.login, repo.name, has_pages)
        return Repository(
            owner=repo.owner.login,
            name=repo.name,
            private=bool(repo.private),
            description=repo.description or "",
            html_url=repo.html_url,
            archived=bool(repo.archived),
            created_at=created,
            updated_at=updated,
            has_pages=has_pages,
            pages_url=pages_url,
        )

    def resolve_pages_url(self, owner: str, name: str) -> str:
        """Best-effort Pages URL (API first, then convention)."""
        try:
            def _resolve() -> str:
                repo = self._gh.get_repo(f"{owner}/{name}")
                if not bool(getattr(repo, "has_pages", False)):
                    return ""
                try:
                    pages = repo.get_pages()
                    url = getattr(pages, "html_url", "") or ""
                    if url:
                        return url
                except GithubException:
                    pass
                return self._guess_pages_url(owner, name, True)

            return self._call(_resolve)
        except GithubException as exc:
            raise self._map_exception(exc) from exc

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
