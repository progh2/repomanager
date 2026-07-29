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
from repomanager.i18n import get_language, tr

PROJECT_URL = "https://github.com/progh2/repomanager"

ABOUT_HTML = {
    "ko": f"""
        <p>수업·실습용으로 쌓인 GitHub 저장소를 한눈에 보고
        아카이브하거나 삭제할 수 있도록 만든 데스크톱 프로그램입니다.</p>
        <p>제작자는 십여 년 동안 소프트웨어 개발을 가르치며
        Git과 GitHub를 이용한 버전 관리를 함께 지도해 왔습니다.
        그 과정에서 수업용으로 만든 저장소가 500개를 넘기게 되었고,
        이를 정리·관리하기 위해 Cursor와 함께 이 프로그램을 만들게 되었습니다.</p>
        <p>프로젝트 저장소:<br><a href="{PROJECT_URL}">{PROJECT_URL}</a></p>
        <p><b>주의</b><br>
        이 프로그램을 사용하면서 발생하는 저장소 삭제·아카이브·공개 범위 변경 등
        모든 결과와 문제는 <b>사용자 본인의 책임</b>입니다.
        되돌릴 수 없는 작업(특히 삭제)은 목록과 설명을 충분히 확인한 뒤
        신중하게 진행해 주세요.</p>
        """,
    "en": f"""
        <p>RepoManager is a desktop app for reviewing, archiving, and deleting
        GitHub repositories created for classes and practice.</p>
        <p>The author has taught software development for over a decade,
        including version control with Git and GitHub. Along the way, more than
        500 class repositories accumulated, so this tool was built with Cursor
        to help manage them.</p>
        <p>Project repository:<br><a href="{PROJECT_URL}">{PROJECT_URL}</a></p>
        <p><b>Disclaimer</b><br>
        Any outcomes or issues from using this program—including deletes,
        archives, and visibility changes—are the <b>user's own responsibility</b>.
        Review lists carefully before irreversible actions (especially delete).</p>
        """,
    "ja": f"""
        <p>授業・実習用に増えた GitHub リポジトリを一覧し、
        アーカイブや削除を行うデスクトップアプリです。</p>
        <p>作者は十数年にわたりソフトウェア開発を教え、
        Git と GitHub によるバージョン管理も指導してきました。
        その過程で授業用リポジトリが 500 を超え、整理のために
        Cursor とともに本プログラムを作りました。</p>
        <p>プロジェクト:<br><a href="{PROJECT_URL}">{PROJECT_URL}</a></p>
        <p><b>注意</b><br>
        本プログラムの利用により生じる削除・アーカイブ・公開設定変更などの
        結果と問題はすべて <b>利用者自身の責任</b>です。
        取り消しできない操作（特に削除）は十分確認のうえ行ってください。</p>
        """,
}


class AboutDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("about.title"))
        self.setMinimumWidth(560)
        self.setMinimumHeight(420)

        title = QLabel(f"RepoManager  v{__version__}")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")

        body = QTextBrowser()
        body.setOpenExternalLinks(True)
        body.setHtml(ABOUT_HTML.get(get_language(), ABOUT_HTML["en"]))

        open_btn = QPushButton(tr("about.open_project"))
        open_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(PROJECT_URL)))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(body, stretch=1)
        layout.addWidget(open_btn)
        layout.addWidget(buttons)
