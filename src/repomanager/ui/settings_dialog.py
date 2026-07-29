"""Settings dialog: PAT, GitHub CLI, and Device Flow login."""

from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
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
    get_oauth_client_id,
    get_saved_token,
    get_use_gh_cli,
    set_oauth_client_id,
    set_saved_token,
    set_use_gh_cli,
    token_source_label,
    try_gh_cli_token,
)
from repomanager.services.oauth_device import (
    OAuthError,
    poll_for_access_token,
    request_device_code,
)


class _DeviceFlowSignals(QObject):
    status = Signal(str)
    finished = Signal(str)  # access token
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
            self.signals.status.emit("Requesting device code...")
            device = request_device_code(self.client_id)
            self.signals.status.emit(
                f"브라우저에서 코드 입력: {device.user_code}\n{device.verification_uri}"
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
            self.signals.error.emit(f"Unexpected error: {exc}")


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(560)
        self._pool = QThreadPool.globalInstance()
        self._device_worker: _DeviceFlowWorker | None = None

        self.source_label = QLabel(f"Current token source: {token_source_label()}")

        # --- PAT ---
        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_edit.setPlaceholderText("ghp_... or github_pat_...")
        saved = get_saved_token()
        if saved:
            self.token_edit.setText(saved)

        self.show_token = QCheckBox("Show token")
        self.show_token.toggled.connect(self._toggle_token_visibility)

        token_row = QHBoxLayout()
        token_row.addWidget(self.token_edit, stretch=1)
        token_row.addWidget(self.show_token)

        pat_box = QGroupBox("Personal Access Token")
        pat_form = QFormLayout(pat_box)
        pat_form.addRow("Token", token_row)
        pat_form.addRow(
            QLabel(
                "Classic: <code>repo</code>, <code>delete_repo</code>, "
                "조직용 <code>read:org</code>"
            )
        )

        # --- gh CLI ---
        self.use_gh = QCheckBox("Prefer token from GitHub CLI (`gh auth token`)")
        self.use_gh.setChecked(get_use_gh_cli())
        import_gh_btn = QPushButton("Import from GitHub CLI now")
        import_gh_btn.clicked.connect(self._import_from_gh)

        gh_box = QGroupBox("GitHub CLI")
        gh_layout = QVBoxLayout(gh_box)
        gh_layout.addWidget(self.use_gh)
        gh_layout.addWidget(import_gh_btn)
        gh_layout.addWidget(
            QLabel("이미 `gh auth login` 되어 있으면 가장 토큰을 재사용할 수 있습니다.")
        )

        # --- Device Flow ---
        self.client_id_edit = QLineEdit()
        self.client_id_edit.setPlaceholderText("OAuth App Client ID (Iv1...)")
        self.client_id_edit.setText(get_oauth_client_id())

        self.device_status = QLabel("")
        self.device_status.setWordWrap(True)

        login_btn = QPushButton("Sign in with GitHub (browser)")
        login_btn.clicked.connect(self._start_device_flow)
        self.cancel_login_btn = QPushButton("Cancel sign-in")
        self.cancel_login_btn.setEnabled(False)
        self.cancel_login_btn.clicked.connect(self._cancel_device_flow)

        login_row = QHBoxLayout()
        login_row.addWidget(login_btn)
        login_row.addWidget(self.cancel_login_btn)

        oauth_box = QGroupBox("Web login (OAuth Device Flow)")
        oauth_layout = QFormLayout(oauth_box)
        oauth_layout.addRow("Client ID", self.client_id_edit)
        oauth_layout.addRow(login_row)
        oauth_layout.addRow(self.device_status)

        help_browser = QTextBrowser()
        help_browser.setOpenExternalLinks(True)
        help_browser.setMaximumHeight(140)
        help_browser.setHtml(
            "<b>웹 로그인</b>은 GitHub OAuth App의 <b>Client ID</b>가 필요합니다.<br>"
            "GitHub → Settings → Developer settings → "
            "<a href='https://github.com/settings/developers'>OAuth Apps</a> → "
            "New OAuth App<br>"
            "Homepage: <code>https://github.com/progh2/repomanager</code><br>"
            "Callback URL: <code>http://127.0.0.1</code> (Device Flow에서는 거의 사용 안 함)<br>"
            "Device Flow를 켠 뒤 Client ID만 여기 붙여넣으면 브라우저로 로그인할 수 있습니다.<br><br>"
            "Client Secret은 데스크톱 앱에 넣지 마세요. Device Flow는 Client ID만으로 동작합니다."
        )

        clear_btn = QPushButton("Clear saved token")
        clear_btn.clicked.connect(self._clear_token)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.source_label)
        layout.addWidget(pat_box)
        layout.addWidget(gh_box)
        layout.addWidget(oauth_box)
        layout.addWidget(help_browser)
        layout.addWidget(clear_btn)
        layout.addWidget(buttons)

    def _toggle_token_visibility(self, checked: bool) -> None:
        mode = (
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )
        self.token_edit.setEchoMode(mode)

    def _import_from_gh(self) -> None:
        token = try_gh_cli_token()
        if not token:
            QMessageBox.warning(
                self,
                "GitHub CLI",
                "`gh auth token`으로 토큰을 가져오지 못했습니다.\n"
                "터미널에서 `gh auth login` 후 다시 시도하세요.",
            )
            return
        self.token_edit.setText(token)
        self.use_gh.setChecked(True)
        QMessageBox.information(self, "GitHub CLI", "토큰을 가져왔습니다. Save를 누르세요.")

    def _clear_token(self) -> None:
        self.token_edit.clear()
        clear_saved_token()
        self.source_label.setText(f"Current token source: {token_source_label()}")
        QMessageBox.information(self, "Settings", "Saved token cleared.")

    def _start_device_flow(self) -> None:
        client_id = self.client_id_edit.text().strip()
        if not client_id:
            QMessageBox.warning(self, "OAuth", "OAuth Client ID를 먼저 입력하세요.")
            return
        set_oauth_client_id(client_id)
        self.cancel_login_btn.setEnabled(True)
        self.device_status.setText("Starting browser sign-in...")

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
        self.device_status.setText("Cancelling...")

    def _on_device_error(self, message: str) -> None:
        self.cancel_login_btn.setEnabled(False)
        self.device_status.setText(message)
        QMessageBox.critical(self, "Sign-in failed", message)

    def _on_device_success(self, token: str) -> None:
        self.cancel_login_btn.setEnabled(False)
        self.token_edit.setText(token)
        self.use_gh.setChecked(False)
        set_saved_token(token)
        self.device_status.setText("Signed in. Token saved.")
        self.source_label.setText(f"Current token source: {token_source_label()}")
        QMessageBox.information(
            self,
            "Signed in",
            "GitHub 웹 로그인에 성공했고 토큰을 저장했습니다.",
        )

    def _save_and_accept(self) -> None:
        set_oauth_client_id(self.client_id_edit.text())
        set_use_gh_cli(self.use_gh.isChecked())
        set_saved_token(self.token_edit.text())
        self.accept()
