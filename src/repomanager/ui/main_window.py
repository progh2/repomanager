"""Main application window."""

from __future__ import annotations

from pathlib import Path

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
from repomanager.ui.about_dialog import AboutDialog
from repomanager.ui.confirm_dialog import ConfirmDialog
from repomanager.ui.dual_repo_lists import DualRepoLists
from repomanager.ui.repo_detail_panel import RepoDetailPanel
from repomanager.ui.settings_dialog import SettingsDialog
from repomanager.workers.api_worker import (
    BulkActionResult,
    BulkActionWorker,
    ListReposWorker,
    LoadResult,
    SuggestDescriptionWorker,
    ToggleVisibilityWorker,
    UpdateDescriptionWorker,
)

DELETE_SCOPE_HINT = (
    "저장소 삭제에는 delete_repo 권한이 필요합니다.\n\n"
    "GitHub CLI를 쓰는 경우 터미널에서 아래를 실행하세요:\n"
    "  gh auth refresh -h github.com -s delete_repo\n\n"
    "또는 설정에서 delete_repo가 포함된 Classic PAT를 저장하세요.\n"
    "(Fine-grained PAT는 Administration: Read and write 필요)"
)

ACTION_LABELS = {
    "archive": "아카이브",
    "unarchive": "활성 복원",
    "delete": "삭제",
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RepoManager")
        self.resize(1200, 820)
        self._pool = QThreadPool.globalInstance()
        self._busy = False
        self._apply_stylesheet()

        self._build_menu()

        self.repo_lists = DualRepoLists()
        self.repo_lists.selection_changed.connect(self._on_selection_changed)
        self.repo_lists.current_repo_changed.connect(self._on_current_repo_changed)
        self.repo_lists.archive_requested.connect(
            lambda repos: self._confirm_action("archive", repos)
        )
        self.repo_lists.unarchive_requested.connect(
            lambda repos: self._confirm_action("unarchive", repos)
        )

        self.detail = RepoDetailPanel()
        self.detail.save_description_requested.connect(self._save_description)
        self.detail.toggle_visibility_requested.connect(self._toggle_visibility)
        self.detail.suggest_description_requested.connect(self._suggest_description)

        self.refresh_btn = QPushButton("새로고침")
        self.refresh_btn.setObjectName("primaryBtn")
        self.refresh_btn.clicked.connect(self.load_repositories)
        self.select_all_btn = QPushButton("전체 선택")
        self.select_all_btn.clicked.connect(self.repo_lists.select_all_visible)
        self.clear_btn = QPushButton("선택 해제")
        self.clear_btn.clicked.connect(self.repo_lists.clear_selection)
        self.delete_btn = QPushButton("선택 삭제")
        self.delete_btn.setObjectName("dangerBtn")
        self.delete_btn.clicked.connect(lambda: self._confirm_action("delete"))
        self.delete_btn.setToolTip(DELETE_SCOPE_HINT)

        self.selection_label = QLabel("선택: 0")

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addWidget(self.select_all_btn)
        toolbar.addWidget(self.clear_btn)
        toolbar.addStretch(1)
        toolbar.addWidget(self.selection_label)
        toolbar.addWidget(self.delete_btn)

        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setVisible(False)

        hint = QLabel(
            "왼쪽=활성, 오른쪽=아카이브. →/← 로 이동하고, 아래 패널에서 설명·공개여부·Pages를 다룹니다."
        )
        hint.setObjectName("hintLabel")
        hint.setWordWrap(True)

        central = QWidget()
        central.setObjectName("centralRoot")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(12)
        layout.addLayout(toolbar)
        layout.addWidget(self.repo_lists, stretch=1)
        layout.addWidget(self.detail)
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

    def _apply_stylesheet(self) -> None:
        qss_path = Path(__file__).with_name("styles.qss")
        if qss_path.is_file():
            self.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    def _build_menu(self) -> None:
        menu = self.menuBar()
        file_menu = menu.addMenu("파일(&F)")

        settings_action = QAction("설정(&S)...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()
        quit_action = QAction("종료(&Q)", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = menu.addMenu("도움말(&H)")
        about_delete = QAction("삭제 권한 안내...", self)
        about_delete.triggered.connect(self.show_delete_permission_help)
        help_menu.addAction(about_delete)
        about_action = QAction("이 프로그램은...(About)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            self._auth_label.setText(f"인증: {token_source_label()}")
            self._set_status("설정을 저장했습니다.")

    def show_about(self) -> None:
        AboutDialog(self).exec()

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
        self.repo_lists.set_repositories(result.repositories)
        self.detail.set_repository(None)
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

    def _on_current_repo_changed(self, repo: object) -> None:
        self.detail.set_repository(repo if isinstance(repo, Repository) else None)

    def _save_description(self, repo: object, description: str) -> None:
        if self._busy or not isinstance(repo, Repository):
            return
        self._set_busy(True, status="설명 저장 중...")
        worker = UpdateDescriptionWorker(repo, description)
        worker.signals.status.connect(self._set_status)
        worker.signals.error.connect(self._on_edit_error)
        worker.signals.finished.connect(self._on_repo_updated)
        self._pool.start(worker)

    def _toggle_visibility(self, repo: object) -> None:
        if self._busy or not isinstance(repo, Repository):
            return
        target = "비공개" if not repo.private else "공개"
        answer = QMessageBox.question(
            self,
            "공개 여부 변경",
            f"{repo.full_name} 저장소를 {target}로 바꿀까요?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            self.detail.set_repository(repo)
            return
        self._set_busy(True, status="공개 여부 변경 중...")
        worker = ToggleVisibilityWorker(repo)
        worker.signals.status.connect(self._set_status)
        worker.signals.error.connect(self._on_edit_error)
        worker.signals.finished.connect(self._on_repo_updated)
        self._pool.start(worker)

    def _suggest_description(self, repo: object) -> None:
        if self._busy or not isinstance(repo, Repository):
            return
        self._set_busy(True, status="AI 추천 준비 중...")
        worker = SuggestDescriptionWorker(repo)
        worker.signals.status.connect(self._set_status)
        worker.signals.error.connect(self._on_suggest_error)
        worker.signals.finished.connect(self._on_suggest_finished)
        self._pool.start(worker)

    def _on_repo_updated(self, repo: object) -> None:
        assert isinstance(repo, Repository)
        self.repo_lists.upsert_repository(repo)
        self.detail.set_repository(repo)
        self._set_busy(False, status=f"{repo.full_name} 정보를 업데이트했습니다.")
        self._set_action_buttons_enabled(True)

    def _on_edit_error(self, message: str) -> None:
        self._set_busy(False, status="수정 실패.")
        self._set_action_buttons_enabled(True)
        QMessageBox.critical(self, "수정 실패", message)

    def _on_suggest_finished(self, text: str) -> None:
        self.detail.apply_suggestion(text)
        self._set_busy(False, status="AI 추천 설명을 반영했습니다. 필요하면 수정 후 저장하세요.")
        self._set_action_buttons_enabled(True)

    def _on_suggest_error(self, message: str) -> None:
        self._set_busy(False, status="AI 추천 실패.")
        self._set_action_buttons_enabled(True)
        QMessageBox.warning(self, "AI 추천", message)

    def _confirm_action(
        self,
        action: str,
        repositories: list[Repository] | None = None,
    ) -> None:
        if self._busy:
            return
        selected = (
            repositories
            if repositories is not None
            else self.repo_lists.selected_repositories()
        )
        if not selected:
            QMessageBox.information(self, "선택 없음", "저장소를 하나 이상 선택하세요.")
            return
        dialog = ConfirmDialog(action=action, repositories=selected, parent=self)
        if dialog.exec() != ConfirmDialog.DialogCode.Accepted:
            return
        self._run_bulk_action(action, selected)

    def _run_bulk_action(self, action: str, repositories: list[Repository]) -> None:
        label = ACTION_LABELS.get(action, action)
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

        action_ko = ACTION_LABELS.get(result.action, result.action)
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
        self.delete_btn.setEnabled(enabled)
        self.repo_lists.setEnabled(enabled)
        self.detail.setEnabled(enabled)

    def _set_status(self, message: str) -> None:
        self.statusBar().showMessage(message)
