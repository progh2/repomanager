"""Background workers for GitHub API calls."""

from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from repomanager.config import ConfigError, get_github_token
from repomanager.i18n import tr
from repomanager.models.repository import Repository
from repomanager.services.github_client import GitHubClient, GitHubClientError, RateLimitInfo


@dataclass
class ActionFailure:
    full_name: str
    message: str


@dataclass
class BulkActionResult:
    action: str
    succeeded: list[str] = field(default_factory=list)
    failed: list[ActionFailure] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return len(self.succeeded)

    @property
    def failure_count(self) -> int:
        return len(self.failed)


@dataclass
class LoadResult:
    repositories: list[Repository]
    login: str
    rate_limit: RateLimitInfo | None = None


class ListSignals(QObject):
    finished = Signal(object)  # LoadResult
    error = Signal(str)
    status = Signal(str)


class BulkSignals(QObject):
    progress = Signal(int, int, str)  # current, total, full_name
    finished = Signal(object)  # BulkActionResult
    error = Signal(str)  # fatal setup errors (token etc.)
    status = Signal(str)
    rate_limit = Signal(object)  # RateLimitInfo | None


class ListReposWorker(QRunnable):
    def __init__(self) -> None:
        super().__init__()
        self.signals = ListSignals()

    @Slot()
    def run(self) -> None:
        try:
            self.signals.status.emit(tr("status.reading_token"))
            token = get_github_token()
            client = GitHubClient(token)
            self.signals.status.emit(tr("status.authenticating"))
            login = client.verify()
            self.signals.status.emit(tr("status.loading_for", login=login))
            repos: list[Repository] = client.list_repositories()
            rate = None
            try:
                rate = client.get_rate_limit()
            except GitHubClientError:
                rate = None
            self.signals.status.emit(tr("status.loaded", login=login, n=len(repos)))
            self.signals.finished.emit(
                LoadResult(repositories=repos, login=login, rate_limit=rate)
            )
        except (ConfigError, GitHubClientError) as exc:
            self.signals.error.emit(str(exc))
        except Exception as exc:  # noqa: BLE001 — surface unexpected errors in UI
            self.signals.error.emit(f"Unexpected error: {exc}")


class BulkActionWorker(QRunnable):
    """Archive or delete repositories one by one, collecting per-repo results."""

    def __init__(self, action: str, repositories: list[Repository]) -> None:
        super().__init__()
        self.action = action.lower()
        self.repositories = list(repositories)
        self.signals = BulkSignals()

    @Slot()
    def run(self) -> None:
        result = BulkActionResult(action=self.action)
        try:
            token = get_github_token()
            client = GitHubClient(token)
        except (ConfigError, GitHubClientError) as exc:
            self.signals.error.emit(str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            self.signals.error.emit(f"Unexpected error: {exc}")
            return

        total = len(self.repositories)
        for index, repo in enumerate(self.repositories, start=1):
            self.signals.progress.emit(index, total, repo.full_name)
            self.signals.status.emit(
                f"{self.action.capitalize()} {repo.full_name} ({index}/{total})"
            )
            try:
                if self.action == "archive":
                    if repo.archived:
                        result.succeeded.append(repo.full_name)
                    else:
                        client.archive_repository(repo.owner, repo.name)
                        result.succeeded.append(repo.full_name)
                elif self.action == "unarchive":
                    if not repo.archived:
                        result.succeeded.append(repo.full_name)
                    else:
                        client.unarchive_repository(repo.owner, repo.name)
                        result.succeeded.append(repo.full_name)
                elif self.action == "delete":
                    client.delete_repository(repo.owner, repo.name)
                    result.succeeded.append(repo.full_name)
                else:
                    result.failed.append(
                        ActionFailure(repo.full_name, f"Unknown action: {self.action}")
                    )
            except GitHubClientError as exc:
                result.failed.append(ActionFailure(repo.full_name, str(exc)))
            except Exception as exc:  # noqa: BLE001
                result.failed.append(
                    ActionFailure(repo.full_name, f"Unexpected error: {exc}")
                )

        try:
            self.signals.rate_limit.emit(client.get_rate_limit())
        except GitHubClientError:
            self.signals.rate_limit.emit(None)

        self.signals.finished.emit(result)


class RepoEditSignals(QObject):
    finished = Signal(object)  # Repository
    error = Signal(str)
    status = Signal(str)


class UpdateDescriptionWorker(QRunnable):
    def __init__(self, repo: Repository, description: str) -> None:
        super().__init__()
        self.repo = repo
        self.description = description
        self.signals = RepoEditSignals()

    @Slot()
    def run(self) -> None:
        try:
            client = GitHubClient(get_github_token())
            self.signals.status.emit(tr("status.saving_desc_name", name=self.repo.full_name))
            updated = client.update_description(
                self.repo.owner, self.repo.name, self.description
            )
            self.signals.finished.emit(updated)
        except (ConfigError, GitHubClientError) as exc:
            self.signals.error.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.signals.error.emit(f"Unexpected error: {exc}")


class ToggleVisibilityWorker(QRunnable):
    def __init__(self, repo: Repository) -> None:
        super().__init__()
        self.repo = repo
        self.signals = RepoEditSignals()

    @Slot()
    def run(self) -> None:
        try:
            client = GitHubClient(get_github_token())
            new_private = not self.repo.private
            label = tr("vis.private") if new_private else tr("vis.public")
            self.signals.status.emit(f"{self.repo.full_name} → {label}")
            updated = client.set_private(self.repo.owner, self.repo.name, new_private)
            self.signals.finished.emit(updated)
        except (ConfigError, GitHubClientError) as exc:
            self.signals.error.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.signals.error.emit(f"Unexpected error: {exc}")


class SuggestSignals(QObject):
    finished = Signal(str)
    error = Signal(str)
    status = Signal(str)


class SuggestDescriptionWorker(QRunnable):
    def __init__(self, repo: Repository) -> None:
        super().__init__()
        self.repo = repo
        self.signals = SuggestSignals()

    @Slot()
    def run(self) -> None:
        try:
            from repomanager.services.ai_assist import (
                CopilotAccessError,
                suggest_repository_description,
            )

            token = get_github_token()
            client = GitHubClient(token)
            self.signals.status.emit(tr("status.ai_checking"))
            readme = client.get_readme_excerpt(self.repo.owner, self.repo.name)
            self.signals.status.emit(tr("status.ai_generating"))
            suggestion = suggest_repository_description(
                token,
                full_name=self.repo.full_name,
                current_description=self.repo.description,
                readme_excerpt=readme,
            )
            self.signals.finished.emit(suggestion)
        except CopilotAccessError as exc:
            self.signals.error.emit(str(exc))
        except (ConfigError, GitHubClientError) as exc:
            self.signals.error.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.signals.error.emit(f"Unexpected error: {exc}")
