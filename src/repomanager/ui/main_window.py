"""Main application window."""

from __future__ import annotations

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from repomanager.models.repository import Repository
from repomanager.services.github_client import RateLimitInfo
from repomanager.ui.confirm_dialog import ConfirmDialog
from repomanager.ui.repo_table import RepoTable
from repomanager.workers.api_worker import (
    BulkActionResult,
    BulkActionWorker,
    ListReposWorker,
    LoadResult,
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RepoManager")
        self.resize(1100, 700)
        self._pool = QThreadPool.globalInstance()
        self._busy = False

        self.repo_table = RepoTable()
        self.repo_table.selection_changed.connect(self._on_selection_changed)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_repositories)
        self.select_all_btn = QPushButton("Select all")
        self.select_all_btn.clicked.connect(self.repo_table.select_all_visible)
        self.clear_btn = QPushButton("Clear selection")
        self.clear_btn.clicked.connect(self.repo_table.clear_selection)
        self.archive_btn = QPushButton("Archive selected")
        self.archive_btn.clicked.connect(lambda: self._confirm_action("archive"))
        self.delete_btn = QPushButton("Delete selected")
        self.delete_btn.clicked.connect(lambda: self._confirm_action("delete"))
        self.delete_btn.setStyleSheet("QPushButton { color: #b00020; }")

        self.selection_label = QLabel("Selected: 0")

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.refresh_btn)
        toolbar.addWidget(self.select_all_btn)
        toolbar.addWidget(self.clear_btn)
        toolbar.addStretch(1)
        toolbar.addWidget(self.selection_label)
        toolbar.addWidget(self.archive_btn)
        toolbar.addWidget(self.delete_btn)

        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setVisible(False)

        hint = QLabel(
            "더블클릭하면 브라우저에서 저장소를 엽니다. "
            "Owner 필터로 개인/조직 저장소를 나눌 수 있습니다. "
            "삭제 전 확인 창에서 DELETE를 입력해야 합니다."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #555;")

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addLayout(toolbar)
        layout.addWidget(self.repo_table, stretch=1)
        layout.addWidget(self.progress)
        layout.addWidget(hint)
        self.setCentralWidget(central)

        status = QStatusBar()
        self.setStatusBar(status)
        self._rate_label = QLabel("API —")
        status.addPermanentWidget(self._rate_label)
        self._set_status("Ready. Click Refresh to load repositories.")

        self._set_action_buttons_enabled(False)

    def load_repositories(self) -> None:
        if self._busy:
            return
        self._set_busy(True, status="Loading...")

        worker = ListReposWorker()
        worker.signals.status.connect(self._set_status)
        worker.signals.error.connect(self._on_load_error)
        worker.signals.finished.connect(self._on_load_finished)
        self._pool.start(worker)

    def _on_load_finished(self, result: object) -> None:
        assert isinstance(result, LoadResult)
        self.repo_table.set_repositories(result.repositories)
        self._update_rate_limit(result.rate_limit)
        self._set_busy(
            False,
            status=f"Loaded {len(result.repositories)} repositories for {result.login}.",
        )
        self._set_action_buttons_enabled(True)

    def _on_load_error(self, message: str) -> None:
        self._set_busy(False, status="Load failed.")
        self._set_action_buttons_enabled(True)
        QMessageBox.critical(self, "GitHub error", message)

    def _on_selection_changed(self, count: int) -> None:
        self.selection_label.setText(f"Selected: {count}")

    def _confirm_action(self, action: str) -> None:
        if self._busy:
            return
        selected = self.repo_table.selected_repositories()
        if not selected:
            QMessageBox.information(self, "No selection", "저장소를 하나 이상 선택하세요.")
            return
        dialog = ConfirmDialog(action=action, repositories=selected, parent=self)
        if dialog.exec() != ConfirmDialog.DialogCode.Accepted:
            return
        self._run_bulk_action(action, selected)

    def _run_bulk_action(self, action: str, repositories: list[Repository]) -> None:
        self._set_busy(True, status=f"Starting {action}...")
        self.progress.setVisible(True)
        self.progress.setMaximum(len(repositories))
        self.progress.setValue(0)

        worker = BulkActionWorker(action, repositories)
        worker.signals.status.connect(self._set_status)
        worker.signals.progress.connect(self._on_bulk_progress)
        worker.signals.error.connect(self._on_bulk_setup_error)
        worker.signals.rate_limit.connect(self._update_rate_limit)
        worker.signals.finished.connect(self._on_bulk_finished)
        self._pool.start(worker)

    def _on_bulk_progress(self, current: int, total: int, full_name: str) -> None:
        self.progress.setMaximum(total)
        self.progress.setValue(current)
        self._set_status(f"Processing {full_name} ({current}/{total})")

    def _on_bulk_setup_error(self, message: str) -> None:
        self.progress.setVisible(False)
        self._set_busy(False, status="Action failed.")
        self._set_action_buttons_enabled(True)
        QMessageBox.critical(self, "GitHub error", message)

    def _on_bulk_finished(self, result: object) -> None:
        assert isinstance(result, BulkActionResult)
        self.progress.setVisible(False)
        self._set_busy(False)
        self._set_action_buttons_enabled(True)

        lines = [
            f"Action: {result.action}",
            f"Succeeded: {result.success_count}",
            f"Failed: {result.failure_count}",
        ]
        if result.failed:
            lines.append("")
            lines.append("Failures:")
            for failure in result.failed:
                lines.append(f"- {failure.full_name}: {failure.message}")

        summary = "\n".join(lines)
        if result.failure_count and result.success_count:
            QMessageBox.warning(self, "Completed with errors", summary)
        elif result.failure_count:
            QMessageBox.critical(self, "Action failed", summary)
        else:
            QMessageBox.information(self, "Completed", summary)

        self._set_status(
            f"{result.action.capitalize()} done — "
            f"{result.success_count} ok, {result.failure_count} failed."
        )
        self.load_repositories()

    def _update_rate_limit(self, info: object) -> None:
        if isinstance(info, RateLimitInfo):
            self._rate_label.setText(info.summary)
        else:
            self._rate_label.setText("API —")

    def _set_busy(self, busy: bool, *, status: str | None = None) -> None:
        self._busy = busy
        self.refresh_btn.setEnabled(not busy)
        if busy:
            self._set_action_buttons_enabled(False)
        if status is not None:
            self._set_status(status)

    def _set_action_buttons_enabled(self, enabled: bool) -> None:
        self.select_all_btn.setEnabled(enabled)
        self.clear_btn.setEnabled(enabled)
        self.archive_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)

    def _set_status(self, message: str) -> None:
        self.statusBar().showMessage(message)
