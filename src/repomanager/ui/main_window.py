"""Main application window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThreadPool, QTimer
from PySide6.QtGui import QAction, QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
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

from repomanager import __version__
from repomanager.i18n import add_listener, remove_listener, tr
from repomanager.config import (
    ConfigError,
    app_settings,
    auto_update_check_due,
    get_github_token,
    get_skipped_update_version,
    mark_update_checked,
    token_source_label,
)
from repomanager.models.repository import Repository
from repomanager.services.github_client import RateLimitInfo
from repomanager.services.repo_cache import load_cache, save_cache
from repomanager.services.updater import UpdateInfo
from repomanager.ui.about_dialog import AboutDialog
from repomanager.ui.confirm_dialog import ConfirmDialog
from repomanager.ui.dual_repo_lists import DualRepoLists
from repomanager.ui.loading_overlay import LoadingOverlay
from repomanager.ui.repo_detail_panel import RepoDetailPanel
from repomanager.ui.rename_dialog import RenameDialog
from repomanager.ui.settings_dialog import SettingsDialog
from repomanager.ui.update_dialog import UpdateDialog
from repomanager.workers.api_worker import (
    BackupRepositoriesWorker,
    BulkActionResult,
    BulkActionWorker,
    ListReposWorker,
    LoadResult,
    RenameRepositoryWorker,
    SuggestDescriptionWorker,
    ToggleVisibilityWorker,
    UpdateDescriptionWorker,
)
from repomanager.workers.update_worker import CheckUpdateWorker

GH_DELETE_CMD = "gh auth refresh -h github.com -s delete_repo"


def action_label(action: str) -> str:
    return tr(f"action.{action}") if action in {"archive", "unarchive", "delete"} else action


class MainWindow(QMainWindow):
    def __init__(self, *, auto_start: bool = True) -> None:
        """``auto_start=False`` skips cache load, token prompt, and update check."""
        super().__init__()
        self.setWindowTitle("RepoManager")
        geometry = app_settings().value("ui/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        else:
            self.resize(1200, 820)
        self._pool = QThreadPool.globalInstance()
        self._busy = False
        self._apply_stylesheet()
        self._file_menu = None
        self._help_menu = None
        self._settings_action = None
        self._quit_action = None
        self._delete_help_action = None
        self._about_action = None
        self._update_action = None
        self._update_check_manual = False

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
        self.repo_lists.delete_requested.connect(
            lambda repos: self._confirm_action("delete", repos)
        )
        self._loading = LoadingOverlay(self.repo_lists)

        for key in ("F5", "Ctrl+R"):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(self.load_repositories)

        self.detail = RepoDetailPanel()
        self.detail.save_description_requested.connect(self._save_description)
        self.detail.toggle_visibility_requested.connect(self._toggle_visibility)
        self.detail.suggest_description_requested.connect(self._suggest_description)
        self.detail.rename_requested.connect(self._rename_repository)
        self.detail.backup_requested.connect(self._backup_one)
        self._rename_from: str | None = None
        self._backup_dir: str | None = None

        self.refresh_btn = QPushButton()
        self.refresh_btn.setObjectName("primaryBtn")
        self.refresh_btn.clicked.connect(self.load_repositories)
        self.select_all_btn = QPushButton()
        self.select_all_btn.clicked.connect(self.repo_lists.select_all_visible)
        self.clear_btn = QPushButton()
        self.clear_btn.clicked.connect(self.repo_lists.clear_selection)
        self.backup_btn = QPushButton()
        self.backup_btn.clicked.connect(self._backup_selected)
        self.delete_btn = QPushButton()
        self.delete_btn.setObjectName("dangerBtn")
        self.delete_btn.clicked.connect(lambda: self._confirm_action("delete"))

        self.selection_label = QLabel()

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addWidget(self.select_all_btn)
        toolbar.addWidget(self.clear_btn)
        toolbar.addWidget(self.backup_btn)
        toolbar.addStretch(1)
        toolbar.addWidget(self.selection_label)
        toolbar.addWidget(self.delete_btn)

        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setVisible(False)

        self.hint = QLabel()
        self.hint.setObjectName("hintLabel")
        self.hint.setWordWrap(True)

        central = QWidget()
        central.setObjectName("centralRoot")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(12)
        layout.addLayout(toolbar)
        layout.addWidget(self.repo_lists, stretch=1)
        layout.addWidget(self.detail)
        layout.addWidget(self.progress)
        layout.addWidget(self.hint)
        self.setCentralWidget(central)

        status = QStatusBar()
        self.setStatusBar(status)
        self._rate_label = QLabel("API —")
        status.addPermanentWidget(self._rate_label)
        self._auth_label = QLabel()
        status.addPermanentWidget(self._auth_label)

        self._set_action_buttons_enabled(False)
        self.retranslate_ui()
        add_listener(self.retranslate_ui)
        if auto_start:
            self._startup()

    def closeEvent(self, event) -> None:  # noqa: N802
        app_settings().setValue("ui/geometry", self.saveGeometry())
        remove_listener(self.retranslate_ui)
        super().closeEvent(event)

    def _startup(self) -> None:
        """Show cached list immediately, then refresh if a token is available."""
        cached = load_cache()
        if cached is not None and cached.repositories:
            self.repo_lists.set_repositories(cached.repositories)
            self._set_action_buttons_enabled(True)
            self._set_status(
                tr("status.cache_shown", time=cached.saved_at.strftime("%Y-%m-%d %H:%M"))
            )
        if auto_update_check_due():
            QTimer.singleShot(3000, lambda: self.check_for_updates(manual=False))
        try:
            get_github_token()
        except ConfigError:
            self._maybe_prompt_settings()
            return
        if cached is not None and cached.repositories:
            QTimer.singleShot(0, self.load_repositories)

    def retranslate_ui(self) -> None:
        self.setWindowTitle(tr("app.name"))
        if self._file_menu is not None:
            self._file_menu.setTitle(tr("menu.file"))
        if self._help_menu is not None:
            self._help_menu.setTitle(tr("menu.help"))
        if self._settings_action is not None:
            self._settings_action.setText(tr("menu.settings"))
        if self._quit_action is not None:
            self._quit_action.setText(tr("menu.quit"))
        if self._delete_help_action is not None:
            self._delete_help_action.setText(tr("menu.delete_help"))
        if self._update_action is not None:
            self._update_action.setText(tr("menu.check_update"))
        if self._about_action is not None:
            self._about_action.setText(tr("menu.about"))
        self.refresh_btn.setText(tr("btn.refresh"))
        self.select_all_btn.setText(tr("btn.select_all"))
        self.clear_btn.setText(tr("btn.clear"))
        self.backup_btn.setText(tr("detail.backup"))
        self.backup_btn.setToolTip(tr("detail.backup_tip"))
        self.delete_btn.setText(tr("btn.delete"))
        self.delete_btn.setToolTip(tr("help.delete_scope"))
        self.hint.setText(tr("hint.main"))
        self._auth_label.setText(tr("auth.label", src=token_source_label()))
        count = len(self.repo_lists.selected_repositories())
        self.selection_label.setText(tr("label.selected", n=count))
        self.repo_lists.retranslate_ui()
        self.detail.retranslate_ui()
        self._set_status(tr("status.ready"))

    def _apply_stylesheet(self) -> None:
        from repomanager.ui.theme import is_dark

        filename = "styles_dark.qss" if is_dark() else "styles.qss"
        qss_path = Path(__file__).with_name(filename)
        if qss_path.is_file():
            self.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    def _build_menu(self) -> None:
        menu = self.menuBar()
        self._file_menu = menu.addMenu(tr("menu.file"))

        self._settings_action = QAction(tr("menu.settings"), self)
        self._settings_action.setShortcut("Ctrl+,")
        self._settings_action.triggered.connect(self.open_settings)
        self._file_menu.addAction(self._settings_action)

        self._file_menu.addSeparator()
        self._quit_action = QAction(tr("menu.quit"), self)
        self._quit_action.setShortcut("Ctrl+Q")
        self._quit_action.triggered.connect(self.close)
        self._file_menu.addAction(self._quit_action)

        self._help_menu = menu.addMenu(tr("menu.help"))
        self._delete_help_action = QAction(tr("menu.delete_help"), self)
        self._delete_help_action.triggered.connect(self.show_delete_permission_help)
        self._help_menu.addAction(self._delete_help_action)
        self._update_action = QAction(tr("menu.check_update"), self)
        self._update_action.triggered.connect(lambda: self.check_for_updates(manual=True))
        self._help_menu.addAction(self._update_action)
        self._about_action = QAction(tr("menu.about"), self)
        self._about_action.triggered.connect(self.show_about)
        self._help_menu.addAction(self._about_action)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            self._apply_stylesheet()
            self.repo_lists.update()
            self._auth_label.setText(tr("auth.label", src=token_source_label()))
            self._set_status(tr("status.settings_saved"))

    def check_for_updates(self, *, manual: bool = True) -> None:
        """Ask GitHub for a newer release; only manual checks report 'up to date'."""
        self._update_check_manual = manual
        mark_update_checked()
        if manual:
            self._set_status(tr("update.checking"))
        worker = CheckUpdateWorker()
        worker.signals.finished.connect(self._on_update_checked)
        worker.signals.error.connect(self._on_update_check_error)
        self._pool.start(worker)

    def _on_update_checked(self, info: object) -> None:
        manual, self._update_check_manual = self._update_check_manual, False
        if not isinstance(info, UpdateInfo):
            if manual:
                self._set_status(tr("update.up_to_date", version=__version__))
                QMessageBox.information(
                    self,
                    tr("update.title"),
                    tr("update.up_to_date", version=__version__),
                )
            return
        if not manual and info.version == get_skipped_update_version():
            return
        UpdateDialog(info, self).exec()

    def _on_update_check_error(self, message: str) -> None:
        # A background check that cannot reach GitHub stays silent.
        manual, self._update_check_manual = self._update_check_manual, False
        if manual:
            self._set_status(message)
            QMessageBox.warning(self, tr("update.failed"), message)

    def show_about(self) -> None:
        AboutDialog(self).exec()

    def show_delete_permission_help(self) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle(tr("delete_help.title"))
        box.setText(tr("delete_help.text"))
        box.setInformativeText(tr("help.delete_scope"))
        copy_btn = box.addButton(tr("delete_help.copy"), QMessageBox.ButtonRole.ActionRole)
        settings_btn = box.addButton(
            tr("delete_help.open_settings"), QMessageBox.ButtonRole.ActionRole
        )
        box.addButton(QMessageBox.StandardButton.Ok)
        box.exec()
        clicked = box.clickedButton()
        if clicked is copy_btn:
            QGuiApplication.clipboard().setText(GH_DELETE_CMD)
            self._set_status(tr("delete_help.copied"))
        elif clicked is settings_btn:
            self.open_settings()

    def _maybe_prompt_settings(self) -> None:
        try:
            get_github_token()
        except ConfigError:
            answer = QMessageBox.question(
                self,
                tr("token.needed_title"),
                tr("token.needed_text"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer == QMessageBox.StandardButton.Yes:
                self.open_settings()

    def load_repositories(self) -> None:
        if self._busy:
            return
        self._set_busy(True, status=tr("status.loading"))
        self._loading.start(tr("status.loading"))

        worker = ListReposWorker()
        worker.signals.status.connect(self._set_status)
        worker.signals.status.connect(self._loading.set_text)
        worker.signals.error.connect(self._on_load_error)
        worker.signals.finished.connect(self._on_load_finished)
        self._pool.start(worker)

    def _on_load_finished(self, result: object) -> None:
        assert isinstance(result, LoadResult)
        self._loading.stop()
        save_cache(result.repositories, result.login)
        self.repo_lists.set_repositories(result.repositories)
        self.detail.set_repository(None)
        self._update_rate_limit(result.rate_limit)
        self._set_busy(
            False,
            status=tr("status.loaded", login=result.login, n=len(result.repositories)),
        )
        self._set_action_buttons_enabled(True)

    def _on_load_error(self, message: str) -> None:
        self._loading.stop()
        self._set_busy(False, status=tr("status.load_failed"))
        self._set_action_buttons_enabled(True)
        QMessageBox.critical(self, tr("err.github_title"), message)

    def _on_selection_changed(self, count: int) -> None:
        self.selection_label.setText(tr("label.selected", n=count))

    def _on_current_repo_changed(self, repo: object) -> None:
        self.detail.set_repository(repo if isinstance(repo, Repository) else None)

    def _save_description(self, repo: object, description: str) -> None:
        if self._busy or not isinstance(repo, Repository):
            return
        self._set_busy(True, status=tr("status.saving_desc"))
        worker = UpdateDescriptionWorker(repo, description)
        worker.signals.status.connect(self._set_status)
        worker.signals.error.connect(self._on_edit_error)
        worker.signals.finished.connect(self._on_repo_updated)
        self._pool.start(worker)

    def _toggle_visibility(self, repo: object) -> None:
        if self._busy or not isinstance(repo, Repository):
            return
        target = tr("vis.private") if not repo.private else tr("vis.public")
        answer = QMessageBox.question(
            self,
            tr("vis.change_title"),
            tr("vis.change_question", name=repo.full_name, target=target),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            self.detail.set_repository(repo)
            return
        self._set_busy(True, status=tr("status.changing_vis"))
        worker = ToggleVisibilityWorker(repo)
        worker.signals.status.connect(self._set_status)
        worker.signals.error.connect(self._on_edit_error)
        worker.signals.finished.connect(self._on_repo_updated)
        self._pool.start(worker)

    def _suggest_description(self, repo: object) -> None:
        if self._busy or not isinstance(repo, Repository):
            return
        self._set_busy(True, status=tr("status.ai_preparing"))
        worker = SuggestDescriptionWorker(repo)
        worker.signals.status.connect(self._set_status)
        worker.signals.error.connect(self._on_suggest_error)
        worker.signals.finished.connect(self._on_suggest_finished)
        self._pool.start(worker)

    def _rename_repository(self, repo: object) -> None:
        if self._busy or not isinstance(repo, Repository):
            return
        if repo.archived:
            return
        dialog = RenameDialog(repo, parent=self)
        if dialog.exec() != RenameDialog.DialogCode.Accepted:
            return
        new_name = dialog.new_repository_name()
        self._rename_from = repo.full_name
        self._set_busy(
            True,
            status=tr("status.renaming", old=repo.full_name, new=new_name),
        )
        worker = RenameRepositoryWorker(repo, new_name)
        worker.signals.status.connect(self._set_status)
        worker.signals.error.connect(self._on_rename_error)
        worker.signals.finished.connect(self._on_repo_renamed)
        self._pool.start(worker)

    def _on_repo_renamed(self, repo: object) -> None:
        assert isinstance(repo, Repository)
        old = self._rename_from
        self._rename_from = None
        self.repo_lists.upsert_repository(repo, replace_full_name=old)
        self.detail.set_repository(repo)
        old_label = old or repo.full_name
        self._set_busy(
            False,
            status=tr("status.renamed", old=old_label, new=repo.full_name),
        )
        self._set_action_buttons_enabled(True)

    def _on_rename_error(self, message: str) -> None:
        self._rename_from = None
        self._set_busy(False, status=tr("status.edit_failed"))
        self._set_action_buttons_enabled(True)
        QMessageBox.critical(self, tr("err.edit_title"), message)

    def _on_repo_updated(self, repo: object) -> None:
        assert isinstance(repo, Repository)
        self.repo_lists.upsert_repository(repo)
        self.detail.set_repository(repo)
        self._set_busy(False, status=tr("status.updated", name=repo.full_name))
        self._set_action_buttons_enabled(True)

    def _on_edit_error(self, message: str) -> None:
        self._set_busy(False, status=tr("status.edit_failed"))
        self._set_action_buttons_enabled(True)
        QMessageBox.critical(self, tr("err.edit_title"), message)

    def _on_suggest_finished(self, text: str) -> None:
        self.detail.apply_suggestion(text)
        self._set_busy(False, status=tr("status.ai_applied"))
        self._set_action_buttons_enabled(True)

    def _on_suggest_error(self, message: str) -> None:
        self._set_busy(False, status=tr("status.ai_failed"))
        self._set_action_buttons_enabled(True)
        QMessageBox.warning(self, tr("ai.title"), message)

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
            QMessageBox.information(self, tr("no_selection_title"), tr("no_selection"))
            return
        dialog = ConfirmDialog(action=action, repositories=selected, parent=self)
        if action == "delete":
            dialog.backup_requested.connect(self._backup_repositories)
        if dialog.exec() != ConfirmDialog.DialogCode.Accepted:
            return
        self._run_bulk_action(action, selected)

    def _backup_one(self, repo: object) -> None:
        if isinstance(repo, Repository):
            self._backup_repositories([repo])

    def _backup_selected(self) -> None:
        selected = self.repo_lists.selected_repositories()
        if not selected:
            QMessageBox.information(self, tr("no_selection_title"), tr("no_selection"))
            return
        self._backup_repositories(selected)

    def _backup_repositories(self, repositories: list) -> None:
        if self._busy:
            return
        repos = [r for r in repositories if isinstance(r, Repository)]
        if not repos:
            return
        directory = QFileDialog.getExistingDirectory(self, tr("backup.choose_dir"))
        if not directory:
            return
        self._backup_dir = directory
        self._set_busy(True, status=tr("status.backing_up", name=repos[0].full_name, current=1, total=len(repos)))
        self.progress.setVisible(True)
        self.progress.setMaximum(len(repos))
        self.progress.setValue(0)
        self._loading.start(tr("status.backing_up", name=repos[0].full_name, current=1, total=len(repos)))

        worker = BackupRepositoriesWorker(repos, directory)
        worker.signals.status.connect(self._set_status)
        worker.signals.status.connect(self._loading.set_text)
        worker.signals.progress.connect(self._on_backup_progress)
        worker.signals.error.connect(self._on_backup_setup_error)
        worker.signals.finished.connect(self._on_backup_finished)
        self._pool.start(worker)

    def _on_backup_progress(self, current: int, total: int, full_name: str) -> None:
        self.progress.setMaximum(total)
        self.progress.setValue(current)
        msg = tr("status.backing_up", name=full_name, current=current, total=total)
        self._set_status(msg)
        self._loading.set_text(msg)

    def _on_backup_setup_error(self, message: str) -> None:
        self.progress.setVisible(False)
        self._loading.stop()
        self._set_busy(False, status=tr("status.action_failed"))
        self._set_action_buttons_enabled(True)
        QMessageBox.critical(self, tr("backup.failed_title"), message)

    def _on_backup_finished(self, results: object) -> None:
        self.progress.setVisible(False)
        self._loading.stop()
        self._set_busy(False)
        self._set_action_buttons_enabled(True)
        assert isinstance(results, list)
        ok = [r for r in results if r[1] and not r[2]]
        fail = [r for r in results if r[2]]
        lines = [
            tr(
                "backup.summary",
                ok=len(ok),
                fail=len(fail),
                dir=self._backup_dir or "",
            )
        ]
        if fail:
            lines.append("")
            lines.append(tr("backup.failed_detail"))
            for full_name, _path, err in fail:
                lines.append(f"- {full_name}: {err}")
        summary = "\n".join(lines)
        if fail and ok:
            QMessageBox.warning(self, tr("backup.partial_title"), summary)
        elif fail:
            QMessageBox.critical(self, tr("backup.failed_title"), summary)
        else:
            QMessageBox.information(self, tr("backup.done_title"), summary)
        self._set_status(tr("status.backup_done", ok=len(ok), fail=len(fail)))

    def _run_bulk_action(self, action: str, repositories: list[Repository]) -> None:
        self._set_busy(True, status=tr("status.action_start", action=action_label(action)))
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
        self._set_status(
            tr("status.action_progress", name=full_name, current=current, total=total)
        )

    def _on_bulk_setup_error(self, message: str) -> None:
        self.progress.setVisible(False)
        self._set_busy(False, status=tr("status.action_failed"))
        self._set_action_buttons_enabled(True)
        QMessageBox.critical(self, tr("err.github_title"), message)

    def _on_bulk_finished(self, result: object) -> None:
        assert isinstance(result, BulkActionResult)
        self.progress.setVisible(False)
        self._set_busy(False)
        self._set_action_buttons_enabled(True)

        label = action_label(result.action)
        lines = [
            tr("result.action", action=label),
            tr("result.success", n=result.success_count),
            tr("result.failure", n=result.failure_count),
        ]
        missing_delete_scope = False
        if result.failed:
            lines.append("")
            lines.append(tr("result.failed_detail"))
            for failure in result.failed:
                lines.append(f"- {failure.full_name}: {failure.message}")
                if "delete_repo" in failure.message:
                    missing_delete_scope = True

        summary = "\n".join(lines)
        if result.failure_count and result.success_count:
            QMessageBox.warning(self, tr("result.partial_title"), summary)
        elif result.failure_count:
            QMessageBox.critical(self, tr("result.failed_title"), summary)
        else:
            QMessageBox.information(self, tr("result.done_title"), summary)

        if missing_delete_scope:
            self.show_delete_permission_help()

        self._set_status(
            tr(
                "status.action_done",
                action=label,
                s=result.success_count,
                f=result.failure_count,
            )
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
        self.backup_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)
        self.repo_lists.setEnabled(enabled)
        self.detail.setEnabled(enabled)

    def _set_status(self, message: str) -> None:
        self.statusBar().showMessage(message)
