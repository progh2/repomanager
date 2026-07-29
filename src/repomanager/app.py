"""Application bootstrap."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from repomanager.i18n import init_language
from repomanager.ui.main_window import MainWindow


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("RepoManager")
    app.setOrganizationName("RepoManager")
    init_language()
    window = MainWindow()
    window.show()
    return app.exec()
