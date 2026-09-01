"""Update dialog: show what's new, download the build, hand off to the installer."""

from __future__ import annotations

from PySide6.QtCore import Qt, QThreadPool, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from repomanager import __version__
from repomanager.config import set_skipped_update_version
from repomanager.i18n import tr
from repomanager.services.updater import (
    UpdateError,
    UpdateInfo,
    can_self_update,
    install,
    is_frozen,
    platform_key,
)
from repomanager.workers.update_worker import DownloadUpdateWorker

MB = 1024 * 1024


class UpdateDialog(QDialog):
    """Presents one available release and, where possible, installs it."""

    def __init__(self, info: UpdateInfo, parent=None) -> None:
        super().__init__(parent)
        self.info = info
        self._pool = QThreadPool.globalInstance()
        self._worker: DownloadUpdateWorker | None = None

        self.setWindowTitle(tr("update.title"))
        self.setMinimumWidth(560)
        self.setMinimumHeight(420)

        title = QLabel(f"RepoManager v{info.version}")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")

        summary = QLabel(tr("update.available", latest=info.version, current=__version__))
        summary.setWordWrap(True)

        notes = QTextBrowser()
        notes.setOpenExternalLinks(True)
        notes.setMarkdown(info.notes or tr("update.no_notes"))

        self.status = QLabel("")
        self.status.setWordWrap(True)
        self.status.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setVisible(False)

        self.install_btn = QPushButton(tr("update.btn_install"))
        self.install_btn.setObjectName("primaryBtn")
        self.install_btn.clicked.connect(self._start_download)
        self.page_btn = QPushButton(tr("update.btn_page"))
        self.page_btn.clicked.connect(self._open_release_page)
        self.skip_btn = QPushButton(tr("update.btn_skip"))
        self.skip_btn.clicked.connect(self._skip_version)
        self.later_btn = QPushButton(tr("update.btn_later"))
        self.later_btn.clicked.connect(self.reject)
        self.cancel_btn = QPushButton(tr("update.btn_cancel"))
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_download)

        self._apply_install_availability()

        buttons = QHBoxLayout()
        buttons.addWidget(self.page_btn)
        buttons.addStretch(1)
        buttons.addWidget(self.cancel_btn)
        buttons.addWidget(self.skip_btn)
        buttons.addWidget(self.later_btn)
        buttons.addWidget(self.install_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(summary)
        layout.addWidget(QLabel(tr("update.notes")))
        layout.addWidget(notes, stretch=1)
        layout.addWidget(self.status)
        layout.addWidget(self.progress)
        layout.addLayout(buttons)

    # --- availability -------------------------------------------------

    def _apply_install_availability(self) -> None:
        """Only offer in-app install when a matching build can replace this one."""
        if not self.info.asset_url:
            self.install_btn.setEnabled(False)
            self.status.setText(tr("update.no_asset", platform=platform_key()))
            return
        if not is_frozen():
            self.install_btn.setEnabled(False)
            self.status.setText(tr("update.source_mode"))
            return
        if not can_self_update():
            self.install_btn.setEnabled(False)
            self.status.setText(tr("update.no_asset", platform=platform_key()))
            return
        if self.info.asset_size:
            self.status.setText(tr("update.size", mb=f"{self.info.asset_size / MB:.1f}"))

    # --- download -----------------------------------------------------

    def _start_download(self) -> None:
        if self._worker is not None:
            return
        answer = QMessageBox.question(
            self,
            tr("update.restart_title"),
            tr("update.restart_text", version=self.info.version),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self._set_downloading(True)
        worker = DownloadUpdateWorker(self.info)
        self._worker = worker
        worker.signals.progress.connect(self._on_progress)
        worker.signals.finished.connect(self._on_downloaded)
        worker.signals.error.connect(self._on_error)
        worker.signals.cancelled.connect(self._on_cancelled)
        self._pool.start(worker)

    def _set_downloading(self, active: bool) -> None:
        self.progress.setVisible(active)
        self.progress.setValue(0)
        self.cancel_btn.setVisible(active)
        self.install_btn.setEnabled(not active)
        self.skip_btn.setEnabled(not active)
        self.later_btn.setEnabled(not active)

    def _cancel_download(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
        self.cancel_btn.setEnabled(False)

    def _on_progress(self, done: int, total: int) -> None:
        if total > 0:
            self.progress.setRange(0, 100)
            self.progress.setValue(int(done * 100 / total))
        else:
            self.progress.setRange(0, 0)  # indeterminate
        self.status.setText(
            tr(
                "update.downloading",
                done=f"{done / MB:.1f}",
                total=f"{total / MB:.1f}" if total else "?",
            )
        )

    def _on_cancelled(self) -> None:
        self._worker = None
        self._set_downloading(False)
        self.cancel_btn.setEnabled(True)
        self.status.setText(tr("update.cancelled"))

    def _on_error(self, message: str) -> None:
        self._worker = None
        self._set_downloading(False)
        self.cancel_btn.setEnabled(True)
        self.status.setText(message)
        QMessageBox.critical(self, tr("update.failed"), message)

    def _on_downloaded(self, path: str) -> None:
        self._worker = None
        self.status.setText(tr("update.installing"))
        try:
            install(path)
        except UpdateError as exc:
            self._on_error(str(exc))
            return
        # The helper is waiting on this process; quitting lets the swap happen.
        self.accept()
        QApplication.instance().quit()

    # --- other actions -------------------------------------------------

    def _open_release_page(self) -> None:
        QDesktopServices.openUrl(QUrl(self.info.html_url))

    def _skip_version(self) -> None:
        set_skipped_update_version(self.info.version)
        self.reject()

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._worker is not None:
            self._worker.cancel()
        super().closeEvent(event)
