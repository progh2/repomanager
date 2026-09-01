"""Settings dialog: PAT, GitHub CLI, and Device Flow login."""

from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from repomanager.config import (
    clear_saved_token,
    get_custom_oauth_client_id,
    get_oauth_client_id,
    get_saved_token,
    get_use_gh_cli,
    set_oauth_client_id,
    set_saved_token,
    set_use_gh_cli,
    token_source_label,
    token_storage_is_secure,
    try_gh_cli_token,
)
from repomanager.i18n import (
    get_saved_language_preference,
    resolve_language,
    set_language,
    set_saved_language_preference,
    tr,
)
from repomanager.services.oauth_device import (
    OAuthError,
    poll_for_access_token,
    request_device_code,
)
from repomanager.ui.theme import get_theme, set_theme

GH_DELETE_CMD = "gh auth refresh -h github.com -s delete_repo"


class _DeviceFlowSignals(QObject):
    status = Signal(str)
    finished = Signal(str)
    error = Signal(str)


class _DeviceFlowWorker(QRunnable):
    def __init__(self, client_id: str) -> None:
        super().__init__()
        self.client_id = client_id
        self.signals = _DeviceFlowSignals()
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @Slot()
    def run(self) -> None:
        try:
            self.signals.status.emit(tr("oauth.requesting"))
            device = request_device_code(self.client_id)
            self.signals.status.emit(
                tr("oauth.enter_code", code=device.user_code, uri=device.verification_uri)
            )
            QDesktopServices.openUrl(QUrl(device.verification_uri))
            token = poll_for_access_token(
                self.client_id,
                device.device_code,
                interval=device.interval,
                expires_in=device.expires_in,
                should_cancel=lambda: self._cancelled,
            )
            self.signals.finished.emit(token)
        except OAuthError as exc:
            self.signals.error.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.signals.error.emit(tr("err.unexpected", exc=exc))


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("settings.title"))
        self.setMinimumWidth(580)
        self._pool = QThreadPool.globalInstance()
        self._device_worker: _DeviceFlowWorker | None = None

        self.source_label = QLabel(tr("settings.token_source", src=token_source_label()))

        # --- Language ---
        self.language_combo = QComboBox()
        self._lang_options = [
            ("auto", tr("settings.lang_auto")),
            ("ko", tr("settings.lang_ko")),
            ("en", tr("settings.lang_en")),
            ("ja", tr("settings.lang_ja")),
        ]
        for code, label in self._lang_options:
            self.language_combo.addItem(label, code)
        pref = get_saved_language_preference()
        idx = max(0, self.language_combo.findData(pref))
        self.language_combo.setCurrentIndex(idx)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem(tr("settings.theme_light"), "light")
        self.theme_combo.addItem(tr("settings.theme_dark"), "dark")
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(get_theme())))

        lang_box = QGroupBox(tr("settings.language"))
        lang_form = QFormLayout(lang_box)
        lang_form.addRow(tr("settings.language"), self.language_combo)
        lang_form.addRow(tr("settings.theme"), self.theme_combo)

        # --- Permission guide ---
        guide = QTextBrowser()
        guide.setOpenExternalLinks(True)
        guide.setMaximumHeight(130)
        guide.setHtml(tr("settings.guide_html", cmd=GH_DELETE_CMD))

        copy_cmd_btn = QPushButton(tr("settings.copy_cmd"))
        copy_cmd_btn.clicked.connect(self._copy_delete_cmd)

        # --- PAT ---
        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_edit.setPlaceholderText(tr("settings.token_placeholder"))
        saved = get_saved_token()
        if saved:
            self.token_edit.setText(saved)

        self.show_token = QCheckBox(tr("settings.show_token"))
        self.show_token.toggled.connect(self._toggle_token_visibility)

        token_row = QHBoxLayout()
        token_row.addWidget(self.token_edit, stretch=1)
        token_row.addWidget(self.show_token)

        storage_note = QLabel(
            tr("settings.token_secure_note")
            if token_storage_is_secure()
            else tr("settings.token_plain_note")
        )
        storage_note.setWordWrap(True)

        pat_box = QGroupBox("Personal Access Token")
        pat_form = QFormLayout(pat_box)
        pat_form.addRow(tr("settings.token_label"), token_row)
        pat_form.addRow(storage_note)

        # --- gh CLI ---
        self.use_gh = QCheckBox(tr("settings.use_gh"))
        self.use_gh.setChecked(get_use_gh_cli())
        import_gh_btn = QPushButton(tr("settings.import_gh"))
        import_gh_btn.clicked.connect(self._import_from_gh)

        gh_box = QGroupBox("GitHub CLI")
        gh_layout = QVBoxLayout(gh_box)
        gh_layout.addWidget(self.use_gh)
        gh_layout.addWidget(import_gh_btn)
        gh_layout.addWidget(copy_cmd_btn)
        gh_note = QLabel(tr("settings.gh_note"))
        gh_note.setWordWrap(True)
        gh_layout.addWidget(gh_note)

        # --- Device Flow (the recommended path: no PAT, no gh CLI) ---
        intro = QLabel(tr("settings.oauth_intro"))
        intro.setWordWrap(True)

        self.device_status = QLabel("")
        self.device_status.setWordWrap(True)

        login_btn = QPushButton(tr("settings.login_web"))
        login_btn.setObjectName("primaryBtn")
        login_btn.clicked.connect(self._start_device_flow)
        self.cancel_login_btn = QPushButton(tr("settings.cancel_login"))
        self.cancel_login_btn.setEnabled(False)
        self.cancel_login_btn.clicked.connect(self._cancel_device_flow)

        login_row = QHBoxLayout()
        login_row.addWidget(login_btn, stretch=1)
        login_row.addWidget(self.cancel_login_btn)

        # Own-OAuth-App support stays available, just out of the way.
        custom_id = get_custom_oauth_client_id()
        self.use_custom_oauth = QCheckBox(tr("settings.oauth_custom"))
        self.use_custom_oauth.setChecked(bool(custom_id))
        self.client_id_edit = QLineEdit()
        self.client_id_edit.setPlaceholderText("OAuth App Client ID")
        self.client_id_edit.setText(custom_id)
        self.client_id_edit.setVisible(bool(custom_id))
        self.use_custom_oauth.toggled.connect(self.client_id_edit.setVisible)

        oauth_box = QGroupBox(tr("settings.oauth_box"))
        oauth_layout = QVBoxLayout(oauth_box)
        oauth_layout.addWidget(intro)
        oauth_layout.addLayout(login_row)
        oauth_layout.addWidget(self.device_status)
        oauth_layout.addWidget(self.use_custom_oauth)
        oauth_layout.addWidget(self.client_id_edit)

        help_browser = QTextBrowser()
        help_browser.setOpenExternalLinks(True)
        help_browser.setMaximumHeight(110)
        help_browser.setHtml(tr("settings.oauth_help_html"))

        clear_btn = QPushButton(tr("settings.clear_token"))
        clear_btn.clicked.connect(self._clear_token)

        buttons = QDialogButtonBox()
        save_btn = buttons.addButton(tr("settings.save"), QDialogButtonBox.ButtonRole.AcceptRole)
        cancel_btn = buttons.addButton(tr("settings.cancel"), QDialogButtonBox.ButtonRole.RejectRole)
        save_btn.clicked.connect(self._save_and_accept)
        cancel_btn.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.source_label)
        layout.addWidget(lang_box)
        layout.addWidget(oauth_box)
        layout.addWidget(help_browser)
        layout.addWidget(guide)
        layout.addWidget(pat_box)
        layout.addWidget(gh_box)
        layout.addWidget(clear_btn)
        layout.addWidget(buttons)

    def _copy_delete_cmd(self) -> None:
        QGuiApplication.clipboard().setText(GH_DELETE_CMD)
        QMessageBox.information(
            self,
            tr("settings.copied_title"),
            tr("settings.copied_text", cmd=GH_DELETE_CMD),
        )

    def _toggle_token_visibility(self, checked: bool) -> None:
        mode = (
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )
        self.token_edit.setEchoMode(mode)

    def _import_from_gh(self) -> None:
        token = try_gh_cli_token()
        if not token:
            QMessageBox.warning(self, "GitHub CLI", tr("settings.gh_import_fail"))
            return
        self.token_edit.setText(token)
        self.use_gh.setChecked(True)
        QMessageBox.information(self, "GitHub CLI", tr("settings.gh_import_ok"))

    def _clear_token(self) -> None:
        self.token_edit.clear()
        clear_saved_token()
        self.source_label.setText(tr("settings.token_source", src=token_source_label()))
        QMessageBox.information(self, tr("settings.title"), tr("settings.cleared"))

    def _start_device_flow(self) -> None:
        if self.use_custom_oauth.isChecked():
            client_id = self.client_id_edit.text().strip()
            if not client_id:
                QMessageBox.warning(self, tr("oauth.title"), tr("oauth.need_client_id"))
                return
            set_oauth_client_id(client_id)
        else:
            set_oauth_client_id("")
            client_id = get_oauth_client_id()
        self.cancel_login_btn.setEnabled(True)
        self.device_status.setText(tr("oauth.starting"))

        worker = _DeviceFlowWorker(client_id)
        self._device_worker = worker
        worker.signals.status.connect(self.device_status.setText)
        worker.signals.error.connect(self._on_device_error)
        worker.signals.finished.connect(self._on_device_success)
        self._pool.start(worker)

    def _cancel_device_flow(self) -> None:
        if self._device_worker is not None:
            self._device_worker.cancel()
        self.cancel_login_btn.setEnabled(False)
        self.device_status.setText(tr("oauth.cancelling"))

    def _on_device_error(self, message: str) -> None:
        self.cancel_login_btn.setEnabled(False)
        self.device_status.setText(message)
        QMessageBox.critical(self, tr("oauth.login_failed"), message)

    def _on_device_success(self, token: str) -> None:
        self.cancel_login_btn.setEnabled(False)
        self.token_edit.setText(token)
        self.use_gh.setChecked(False)
        set_saved_token(token)
        self.device_status.setText(tr("oauth.login_done"))
        self.source_label.setText(tr("settings.token_source", src=token_source_label()))
        QMessageBox.information(
            self, tr("oauth.login_ok_title"), tr("oauth.login_ok_text")
        )

    def _save_and_accept(self) -> None:
        set_oauth_client_id(
            self.client_id_edit.text() if self.use_custom_oauth.isChecked() else ""
        )
        set_use_gh_cli(self.use_gh.isChecked())
        set_saved_token(self.token_edit.text())
        set_theme(str(self.theme_combo.currentData() or "light"))
        pref = str(self.language_combo.currentData() or "auto")
        set_saved_language_preference(pref)
        set_language(resolve_language(pref), notify=True)
        self.accept()
