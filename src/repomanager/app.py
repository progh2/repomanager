"""Application bootstrap."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from repomanager.i18n import init_language
from repomanager.ui.main_window import MainWindow

ICON_PATH = Path(__file__).parent / "ui" / "assets" / "icon.png"


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("RepoManager")
    app.setOrganizationName("RepoManager")
    if ICON_PATH.is_file():
        app.setWindowIcon(QIcon(str(ICON_PATH)))
    init_language()
    window = MainWindow()
    window.show()
    return app.exec()
