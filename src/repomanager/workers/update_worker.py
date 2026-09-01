"""Background workers for the self-update flow."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from repomanager import __version__
from repomanager.i18n import tr
from repomanager.services.updater import (
    UpdateError,
    UpdateInfo,
    check_for_update,
    download_asset,
)


class CheckUpdateSignals(QObject):
    finished = Signal(object)  # UpdateInfo | None
    error = Signal(str)


class CheckUpdateWorker(QRunnable):
    """Ask GitHub Releases whether a newer build exists."""

    def __init__(self, current_version: str = __version__) -> None:
        super().__init__()
        self.current_version = current_version
        self.signals = CheckUpdateSignals()

    @Slot()
    def run(self) -> None:
        try:
            self.signals.finished.emit(check_for_update(self.current_version))
        except UpdateError as exc:
            self.signals.error.emit(str(exc))
        except Exception as exc:  # noqa: BLE001 — surface unexpected errors in UI
            self.signals.error.emit(tr("err.unexpected", exc=exc))


class DownloadUpdateSignals(QObject):
    progress = Signal(int, int)  # downloaded bytes, total bytes
    finished = Signal(str)  # path to the downloaded artifact
    error = Signal(str)
    cancelled = Signal()


class DownloadUpdateWorker(QRunnable):
    """Stream the release asset to disk, reporting progress."""

    def __init__(self, info: UpdateInfo) -> None:
        super().__init__()
        self.info = info
        self.signals = DownloadUpdateSignals()
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @Slot()
    def run(self) -> None:
        try:
            path: Path = download_asset(
                self.info,
                progress=self.signals.progress.emit,
                should_cancel=lambda: self._cancelled,
            )
        except UpdateError as exc:
            if self._cancelled:
                self.signals.cancelled.emit()
            else:
                self.signals.error.emit(str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            self.signals.error.emit(tr("err.unexpected", exc=exc))
            return
        self.signals.finished.emit(str(path))
