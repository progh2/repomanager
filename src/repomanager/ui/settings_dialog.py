"""Settings dialog: PAT, GitHub CLI, and Device Flow login."""

from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication
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
            self.signals.status.emit("기기 코드를 요청하는 중...")
            device = request_device_code(self.client_id)
            self.signals.status.emit(
                f"브라우저에서 이 코드를 입력하세요: {device.user_code}\n"
                f"{device.verification_uri}"
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
            self.signals.error.emit(f"예상치 못한 오류: {exc}")


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("설정")
        self.setMinimumWidth(580)
        self._pool = QThreadPool.globalInstance()
        self._device_worker: _DeviceFlowWorker | None = None

        self.source_label = QLabel(f"현재 토큰 출처: {token_source_label()}")

        # --- Permission guide ---
        guide = QTextBrowser()
        guide.setOpenExternalLinks(True)
        guide.setMaximumHeight(130)
        guide.setHtml(
            "<b>삭제(Delete)를 쓰려면</b> 토큰에 <code>delete_repo</code> 권한이 있어야 합니다.<br>"
            "목록 조회·아카이브는 <code>repo</code>만으로도 되지만, 삭제는 별도 권한입니다.<br><br>"
            "<b>GitHub CLI 사용자</b> — 터미널에서 실행 후 이 창에서 다시 가져오세요:<br>"
            f"<code>{GH_DELETE_CMD}</code><br><br>"
            "<b>PAT 사용자</b> — Classic 토큰 생성 시 "
            "<code>repo</code> + <code>delete_repo</code> (+ 조직이면 <code>read:org</code>) 체크.<br>"
            "Fine-grained는 대상 저장소에 <b>Administration: Read and write</b>."
        )

        copy_cmd_btn = QPushButton("삭제 권한 명령 복사")
        copy_cmd_btn.clicked.connect(self._copy_delete_cmd)

        # --- PAT ---
        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_edit.setPlaceholderText("ghp_... 또는 github_pat_...")
        saved = get_saved_token()
        if saved:
            self.token_edit.setText(saved)

        self.show_token = QCheckBox("토큰 표시")
        self.show_token.toggled.connect(self._toggle_token_visibility)

        token_row = QHBoxLayout()
        token_row.addWidget(self.token_edit, stretch=1)
        token_row.addWidget(self.show_token)

        pat_box = QGroupBox("Personal Access Token")
        pat_form = QFormLayout(pat_box)
        pat_form.addRow("토큰", token_row)

        # --- gh CLI ---
        self.use_gh = QCheckBox("GitHub CLI 토큰을 우선 사용 (gh auth token)")
        self.use_gh.setChecked(get_use_gh_cli())
        import_gh_btn = QPushButton("GitHub CLI에서 지금 가져오기")
        import_gh_btn.clicked.connect(self._import_from_gh)

        gh_box = QGroupBox("GitHub CLI")
        gh_layout = QVBoxLayout(gh_box)
        gh_layout.addWidget(self.use_gh)
        gh_layout.addWidget(import_gh_btn)
        gh_layout.addWidget(copy_cmd_btn)
        gh_note = QLabel(
            "기본 gh 로그인에는 보통 delete_repo가 없습니다. "
            "위에서 명령을 복사해 실행한 뒤 「가져오기」를 다시 누르세요."
        )
        gh_note.setWordWrap(True)
        gh_layout.addWidget(gh_note)

        # --- Device Flow ---
        self.client_id_edit = QLineEdit()
        self.client_id_edit.setPlaceholderText("OAuth App Client ID")
        self.client_id_edit.setText(get_oauth_client_id())

        self.device_status = QLabel("")
        self.device_status.setWordWrap(True)

        login_btn = QPushButton("GitHub 웹으로 로그인")
        login_btn.clicked.connect(self._start_device_flow)
        self.cancel_login_btn = QPushButton("로그인 취소")
        self.cancel_login_btn.setEnabled(False)
        self.cancel_login_btn.clicked.connect(self._cancel_device_flow)

        login_row = QHBoxLayout()
        login_row.addWidget(login_btn)
        login_row.addWidget(self.cancel_login_btn)

        oauth_box = QGroupBox("웹 로그인 (OAuth Device Flow)")
        oauth_layout = QFormLayout(oauth_box)
        oauth_layout.addRow("Client ID", self.client_id_edit)
        oauth_layout.addRow(login_row)
        oauth_layout.addRow(self.device_status)

        help_browser = QTextBrowser()
        help_browser.setOpenExternalLinks(True)
        help_browser.setMaximumHeight(110)
        help_browser.setHtml(
            "웹 로그인은 "
            "<a href='https://github.com/settings/developers'>OAuth App</a>의 "
            "Client ID가 필요합니다. Device Flow를 켠 뒤 Client ID만 입력하세요. "
            "Client Secret은 앱에 넣지 마세요."
        )

        clear_btn = QPushButton("저장된 토큰 지우기")
        clear_btn.clicked.connect(self._clear_token)

        buttons = QDialogButtonBox()
        save_btn = buttons.addButton("저장", QDialogButtonBox.ButtonRole.AcceptRole)
        cancel_btn = buttons.addButton("취소", QDialogButtonBox.ButtonRole.RejectRole)
        save_btn.clicked.connect(self._save_and_accept)
        cancel_btn.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.source_label)
        layout.addWidget(guide)
        layout.addWidget(pat_box)
        layout.addWidget(gh_box)
        layout.addWidget(oauth_box)
        layout.addWidget(help_browser)
        layout.addWidget(clear_btn)
        layout.addWidget(buttons)

    def _copy_delete_cmd(self) -> None:
        QGuiApplication.clipboard().setText(GH_DELETE_CMD)
        QMessageBox.information(
            self,
            "복사됨",
            f"아래 명령을 클립보드에 복사했습니다.\n\n{GH_DELETE_CMD}\n\n"
            "터미널에서 실행한 뒤 「GitHub CLI에서 지금 가져오기」를 누르세요.",
        )

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
                "gh auth token으로 토큰을 가져오지 못했습니다.\n"
                "터미널에서 gh auth login 후 다시 시도하세요.",
            )
            return
        self.token_edit.setText(token)
        self.use_gh.setChecked(True)
        QMessageBox.information(
            self,
            "GitHub CLI",
            "토큰을 가져왔습니다. 「저장」을 누르세요.\n"
            "삭제가 403이면 먼저 delete_repo 권한 명령을 실행하세요.",
        )

    def _clear_token(self) -> None:
        self.token_edit.clear()
        clear_saved_token()
        self.source_label.setText(f"현재 토큰 출처: {token_source_label()}")
        QMessageBox.information(self, "설정", "저장된 토큰을 지웠습니다.")

    def _start_device_flow(self) -> None:
        client_id = self.client_id_edit.text().strip()
        if not client_id:
            QMessageBox.warning(self, "OAuth", "OAuth Client ID를 먼저 입력하세요.")
            return
        set_oauth_client_id(client_id)
        self.cancel_login_btn.setEnabled(True)
        self.device_status.setText("브라우저 로그인을 시작하는 중...")

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
        self.device_status.setText("취소하는 중...")

    def _on_device_error(self, message: str) -> None:
        self.cancel_login_btn.setEnabled(False)
        self.device_status.setText(message)
        QMessageBox.critical(self, "로그인 실패", message)

    def _on_device_success(self, token: str) -> None:
        self.cancel_login_btn.setEnabled(False)
        self.token_edit.setText(token)
        self.use_gh.setChecked(False)
        set_saved_token(token)
        self.device_status.setText("로그인 완료. 토큰을 저장했습니다.")
        self.source_label.setText(f"현재 토큰 출처: {token_source_label()}")
        QMessageBox.information(
            self,
            "로그인 성공",
            "GitHub 웹 로그인에 성공했고 토큰을 저장했습니다.\n"
            "삭제를 쓰려면 OAuth App 권한에 delete_repo가 포함돼야 합니다.",
        )

    def _save_and_accept(self) -> None:
        set_oauth_client_id(self.client_id_edit.text())
        set_use_gh_cli(self.use_gh.isChecked())
        set_saved_token(self.token_edit.text())
        self.accept()
