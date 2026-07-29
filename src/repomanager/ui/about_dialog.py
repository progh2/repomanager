"""About dialog."""

from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from repomanager import __version__

PROJECT_URL = "https://github.com/progh2/repomanager"


class AboutDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("이 프로그램은...")
        self.setMinimumWidth(560)
        self.setMinimumHeight(420)

        title = QLabel(f"RepoManager  v{__version__}")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")

        body = QTextBrowser()
        body.setOpenExternalLinks(True)
        body.setHtml(
            f"""
            <p>수업·실습용으로 쌓인 GitHub 저장소를 한눈에 보고
            아카이브하거나 삭제할 수 있도록 만든 데스크톱 프로그램입니다.</p>

            <p>제작자는 십여 년 동안 소프트웨어 개발을 가르치며
            Git과 GitHub를 이용한 버전 관리를 함께 지도해 왔습니다.
            그 과정에서 수업용으로 만든 저장소가 500개를 넘기게 되었고,
            이를 정리·관리하기 위해 Cursor와 함께 이 프로그램을 만들게 되었습니다.</p>

            <p>프로젝트 저장소:<br>
            <a href="{PROJECT_URL}">{PROJECT_URL}</a></p>

            <p><b>주의</b><br>
            이 프로그램을 사용하면서 발생하는 저장소 삭제·아카이브·공개 범위 변경 등
            모든 결과와 문제는 <b>사용자 본인의 책임</b>입니다.
            되돌릴 수 없는 작업(특히 삭제)은 목록과 설명을 충분히 확인한 뒤
            신중하게 진행해 주세요.</p>
            """
        )

        open_btn = QPushButton("프로젝트 GitHub 열기")
        open_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(PROJECT_URL)))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(body, stretch=1)
        layout.addWidget(open_btn)
        layout.addWidget(buttons)
