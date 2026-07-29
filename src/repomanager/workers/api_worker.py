"""Background workers for GitHub API calls."""

from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from repomanager.config import ConfigError, get_github_token
from repomanager.models.repository import Repository
from repomanager.services.github_client import GitHubClient, GitHubClientError


class WorkerSignals(QObject):
    finished = Signal(list)  # list[Repository]
    error = Signal(str)
    status = Signal(str)


class ListReposWorker(QRunnable):
    def __init__(self) -> None:
        super().__init__()
        self.signals = WorkerSignals()

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
