"""Application bootstrap."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from repomanager import __version__
from repomanager.i18n import init_language
from repomanager.ui.main_window import MainWindow

ICON_PATH = Path(__file__).parent / "ui" / "assets" / "icon.png"


def _make_app(argv: list[str]) -> QApplication:
    app = QApplication(argv)
    app.setApplicationName("RepoManager")
    app.setOrganizationName("RepoManager")
    app.setApplicationVersion(__version__)
    if ICON_PATH.is_file():
        app.setWindowIcon(QIcon(str(ICON_PATH)))
    return app


def selftest(argv: list[str] | None = None) -> int:
    """Build the whole UI once and exit — no window, no dialogs, no network.

    Packaged builds run this in CI. A missing Qt plugin, an uncollected
    dependency, or a bad data-file path fails here with a non-zero exit code
    instead of surfacing as a dialog on a user's machine.
    """
    argv = list(sys.argv if argv is None else argv)
    app = _make_app(argv)
    init_language()
    window = MainWindow(auto_start=False)
    window.close()
    app.quit()
    print(f"RepoManager {__version__} selftest OK")
    return 0


def run(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    if "--selftest" in argv:
        return selftest(argv)
    if "--version" in argv:
        print(f"RepoManager {__version__}")
        return 0
    app = _make_app(argv)
    init_language()
    window = MainWindow()
    window.show()
    return app.exec()
