"""Main application window."""

from __future__ import annotations

from PySide6.QtCore import QThreadPool
from PySide6.QtGui import QAction, QGuiApplication
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

from repomanager.config import ConfigError, get_github_token, token_source_label
from repomanager.models.repository import Repository
from repomanager.services.github_client import RateLimitInfo
from repomanager.ui.confirm_dialog import ConfirmDialog
from repomanager.ui.repo_table import RepoTable
from repomanager.ui.settings_dialog import SettingsDialog
from repomanager.workers.api_worker import (
    BulkActionResult,
    BulkActionWorker,
    ListReposWorker,
    LoadResult,
)

DELETE_SCOPE_HINT = (
    "저장소 삭제에는 delete_repo 권한이 필요합니다.\n\n"
    "GitHub CLI를 쓰는 경우 터미널에서 아래를 실행하세요:\n"
    "  gh auth refresh -h github.com -s delete_repo\n\n"
    "또는 설정에서 delete_repo가 포함된 Classic PAT를 저장하세요.\n"
    "(Fine-grained PAT는 Administration: Read and write 필요)"
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RepoManager")
        self.resize(1100, 700)
        self._pool = QThreadPool.globalInstance()
        self._busy = False

        self._build_menu()

        self.repo_table = RepoTable()
        self.repo_table.selection_changed.connect(self._on_selection_changed)

        self.refresh_btn = QPushButton("새로고침")
        self.refresh_btn.clicked.connect(self.load_repositories)
        self.select_all_btn = QPushButton("전체 선택")
        self.select_all_btn.clicked.connect(self.repo_table.select_all_visible)
        self.clear_btn = QPushButton("선택 해제")
        self.clear_btn.clicked.connect(self.repo_table.clear_selection)
        self.archive_btn = QPushButton("선택 아카이브")
        self.archive_btn.clicked.connect(lambda: self._confirm_action("archive"))
        self.delete_btn = QPushButton("선택 삭제")
        self.delete_btn.clicked.connect(lambda: self._confirm_action("delete"))
        self.delete_btn.setStyleSheet("QPushButton { color: #b00020; }")
        self.delete_btn.setToolTip(DELETE_SCOPE_HINT)

        self.selection_label = QLabel("선택: 0")

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
            "파일 → 설정에서 토큰을 구성하세요. "
            "「열기」또는 행 더블클릭으로 GitHub 페이지를 엽니다. "
            "삭제 시 DELETE 입력이 필요하며, delete_repo 권한이 있어야 합니다."
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
        self._auth_label = QLabel(f"인증: {token_source_label()}")
        status.addPermanentWidget(self._auth_label)
        self._set_status("준비됨. 필요하면 설정을 연 뒤 새로고침하세요.")

        self._set_action_buttons_enabled(False)
        self._maybe_prompt_settings()

    def _build_menu(self) -> None:
        menu = self.menuBar()
        file_menu = menu.addMenu("파일(&F)")

        settings_action = QAction("설정(&S)...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)

        help_delete = QAction("삭제 권한 안내(&D)...", self)
        help_delete.triggered.connect(self.show_delete_permission_help)
        file_menu.addAction(help_delete)

        file_menu.addSeparator()
        quit_action = QAction("종료(&Q)", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = menu.addMenu("도움말(&H)")
        about_delete = QAction("삭제 권한 안내...", self)
        about_delete.triggered.connect(self.show_delete_permission_help)
        help_menu.addAction(about_delete)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            self._auth_label.setText(f"인증: {token_source_label()}")
            self._set_status("설정을 저장했습니다.")

    def show_delete_permission_help(self) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle("삭제 권한 안내")
        box.setText("저장소를 삭제하려면 delete_repo 권한이 필요합니다.")
        box.setInformativeText(DELETE_SCOPE_HINT)
        copy_btn = box.addButton("명령 복사", QMessageBox.ButtonRole.ActionRole)
        settings_btn = box.addButton("설정 열기", QMessageBox.ButtonRole.ActionRole)
        box.addButton(QMessageBox.StandardButton.Ok)
        box.exec()
        clicked = box.clickedButton()
        if clicked is copy_btn:
            QGuiApplication.clipboard().setText(
                "gh auth refresh -h github.com -s delete_repo"
            )
            self._set_status("삭제 권한 명령을 클립보드에 복사했습니다.")
        elif clicked is settings_btn:
            self.open_settings()

    def _maybe_prompt_settings(self) -> None:
        try:
            get_github_token()
        except ConfigError:
            answer = QMessageBox.question(
                self,
                "GitHub 토큰 필요",
                "GitHub 토큰이 아직 없습니다.\n"
                "설정에서 PAT 입력, GitHub CLI, 또는 웹 로그인을 구성할까요?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer == QMessageBox.StandardButton.Yes:
                self.open_settings()

    def load_repositories(self) -> None:
        if self._busy:
            return
        self._set_busy(True, status="불러오는 중...")

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
            status=f"{result.login} 저장소 {len(result.repositories)}개를 불러왔습니다.",
        )
        self._set_action_buttons_enabled(True)

    def _on_load_error(self, message: str) -> None:
        self._set_busy(False, status="불러오기 실패.")
        self._set_action_buttons_enabled(True)
        QMessageBox.critical(self, "GitHub 오류", message)

    def _on_selection_changed(self, count: int) -> None:
        self.selection_label.setText(f"선택: {count}")

    def _confirm_action(self, action: str) -> None:
        if self._busy:
            return
        selected = self.repo_table.selected_repositories()
        if not selected:
            QMessageBox.information(self, "선택 없음", "저장소를 하나 이상 선택하세요.")
            return
        dialog = ConfirmDialog(action=action, repositories=selected, parent=self)
        if dialog.exec() != ConfirmDialog.DialogCode.Accepted:
            return
        self._run_bulk_action(action, selected)

    def _run_bulk_action(self, action: str, repositories: list[Repository]) -> None:
        label = "아카이브" if action == "archive" else "삭제"
        self._set_busy(True, status=f"{label} 시작...")
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
        self._set_status(f"처리 중 {full_name} ({current}/{total})")

    def _on_bulk_setup_error(self, message: str) -> None:
        self.progress.setVisible(False)
        self._set_busy(False, status="작업 실패.")
        self._set_action_buttons_enabled(True)
        QMessageBox.critical(self, "GitHub 오류", message)

    def _on_bulk_finished(self, result: object) -> None:
        assert isinstance(result, BulkActionResult)
        self.progress.setVisible(False)
        self._set_busy(False)
        self._set_action_buttons_enabled(True)

        action_ko = "아카이브" if result.action == "archive" else "삭제"
        lines = [
            f"작업: {action_ko}",
            f"성공: {result.success_count}",
            f"실패: {result.failure_count}",
        ]
        missing_delete_scope = False
        if result.failed:
            lines.append("")
            lines.append("실패 상세:")
            for failure in result.failed:
                lines.append(f"- {failure.full_name}: {failure.message}")
                if "delete_repo" in failure.message:
                    missing_delete_scope = True

        summary = "\n".join(lines)
        if result.failure_count and result.success_count:
            QMessageBox.warning(self, "일부 실패", summary)
        elif result.failure_count:
            QMessageBox.critical(self, "작업 실패", summary)
        else:
            QMessageBox.information(self, "완료", summary)

        if missing_delete_scope:
            self.show_delete_permission_help()

        self._set_status(
            f"{action_ko} 완료 — 성공 {result.success_count}, 실패 {result.failure_count}."
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
