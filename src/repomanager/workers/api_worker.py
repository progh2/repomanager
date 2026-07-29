"""Background workers for GitHub API calls."""

from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from repomanager.config import ConfigError, get_github_token
from repomanager.models.repository import Repository
from repomanager.services.github_client import GitHubClient, GitHubClientError


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


class ListSignals(QObject):
    finished = Signal(list)  # list[Repository]
    error = Signal(str)
    status = Signal(str)


class BulkSignals(QObject):
    progress = Signal(int, int, str)  # current, total, full_name
    finished = Signal(object)  # BulkActionResult
    error = Signal(str)  # fatal setup errors (token etc.)
    status = Signal(str)


class ListReposWorker(QRunnable):
    def __init__(self) -> None:
        super().__init__()
        self.signals = ListSignals()

    @Slot()
    def run(self) -> None:
        try:
            self.signals.status.emit("Reading token...")
            token = get_github_token()
            client = GitHubClient(token)
            self.signals.status.emit("Authenticating...")
            login = client.verify()
            self.signals.status.emit(f"Loading repositories for {login}...")
            repos: list[Repository] = client.list_repositories()
            self.signals.status.emit(f"Loaded {len(repos)} repositories.")
            self.signals.finished.emit(repos)
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
            self.signals.status.emit(f"{self.action.capitalize()} {repo.full_name} ({index}/{total})")
            try:
                if self.action == "archive":
                    if repo.archived:
                        result.succeeded.append(repo.full_name)
                    else:
                        client.archive_repository(repo.owner, repo.name)
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
                result.failed.append(ActionFailure(repo.full_name, f"Unexpected error: {exc}"))

        self.signals.finished.emit(result)
