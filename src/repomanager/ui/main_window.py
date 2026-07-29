"""Main application window."""

from __future__ import annotations

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from repomanager.models.repository import Repository
from repomanager.ui.confirm_dialog import ConfirmDialog
from repomanager.ui.repo_table import RepoTable
from repomanager.workers.api_worker import ListReposWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RepoManager")
        self.resize(1100, 700)
        self._pool = QThreadPool.globalInstance()
        self._loading = False

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

        hint = QLabel(
            "더블클릭하면 브라우저에서 저장소를 엽니다. "
            "Archive/Delete API 실행은 Milestone 4에서 연결됩니다 — 지금은 확인 창까지 동작합니다."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #555;")

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addLayout(toolbar)
        layout.addWidget(self.repo_table, stretch=1)
        layout.addWidget(hint)
        self.setCentralWidget(central)

        status = QStatusBar()
        self.setStatusBar(status)
        self._set_status("Ready. Click Refresh to load repositories.")

        self._set_action_buttons_enabled(False)

    def load_repositories(self) -> None:
        if self._loading:
            return
        self._loading = True
        self.refresh_btn.setEnabled(False)
        self._set_status("Loading...")

        worker = ListReposWorker()
        worker.signals.status.connect(self._set_status)
        worker.signals.error.connect(self._on_load_error)
        worker.signals.finished.connect(self._on_load_finished)
        self._pool.start(worker)

    def _on_load_finished(self, repos: list) -> None:
        self._loading = False
        self.refresh_btn.setEnabled(True)
        typed: list[Repository] = list(repos)
        self.repo_table.set_repositories(typed)
        self._set_status(f"Loaded {len(typed)} repositories.")
        self._set_action_buttons_enabled(True)

    def _on_load_error(self, message: str) -> None:
        self._loading = False
        self.refresh_btn.setEnabled(True)
        self._set_status("Load failed.")
        QMessageBox.critical(self, "GitHub error", message)

    def _on_selection_changed(self, count: int) -> None:
        self.selection_label.setText(f"Selected: {count}")

    def _confirm_action(self, action: str) -> None:
        selected = self.repo_table.selected_repositories()
        if not selected:
            QMessageBox.information(self, "No selection", "저장소를 하나 이상 선택하세요.")
            return
        dialog = ConfirmDialog(action=action, repositories=selected, parent=self)
        if dialog.exec() != ConfirmDialog.DialogCode.Accepted:
            return
        QMessageBox.information(
            self,
            "Not implemented yet",
            f"{action.capitalize()} API 실행은 Milestone 4에서 구현됩니다.\n"
            f"확인된 저장소: {len(selected)}개",
        )

    def _set_action_buttons_enabled(self, enabled: bool) -> None:
        self.select_all_btn.setEnabled(enabled)
        self.clear_btn.setEnabled(enabled)
        self.archive_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)

    def _set_status(self, message: str) -> None:
        self.statusBar().showMessage(message)
