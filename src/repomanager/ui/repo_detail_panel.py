"""Selected repository detail / edit panel."""

from __future__ import annotations

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from repomanager.models.repository import Repository


class RepoDetailPanel(QFrame):
    save_description_requested = Signal(object, str)  # repo, description
    toggle_visibility_requested = Signal(object)  # repo
    suggest_description_requested = Signal(object)  # repo

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("detailPane")
        self._repo: Repository | None = None

        self.title = QLabel("저장소를 선택하세요")
        self.title.setObjectName("paneTitle")
        self.meta = QLabel("")
        self.meta.setObjectName("hintLabel")
        self.meta.setWordWrap(True)

        self.visibility_btn = QPushButton("공개")
        self.visibility_btn.setObjectName("toggleBtn")
        self.visibility_btn.setCheckable(True)
        self.visibility_btn.clicked.connect(self._on_visibility_clicked)

        self.pages_label = QLabel("GitHub Pages: 없음")
        self.pages_btn = QPushButton("Pages 열기")
        self.pages_btn.setObjectName("secondaryBtn")
        self.pages_btn.clicked.connect(self._open_pages)

        self.open_repo_btn = QPushButton("저장소 열기")
        self.open_repo_btn.setObjectName("secondaryBtn")
        self.open_repo_btn.clicked.connect(self._open_repo)

        top = QHBoxLayout()
        top.addWidget(self.title, stretch=1)
        top.addWidget(self.visibility_btn)
        top.addWidget(self.open_repo_btn)
        top.addWidget(self.pages_btn)

        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("저장소 설명을 입력하세요...")
        self.desc_edit.setMaximumHeight(90)

        self.suggest_btn = QPushButton("AI 추천 설명")
        self.suggest_btn.setToolTip(
            "GitHub Models / Copilot 권한이 있으면 README 등을 보고 설명을 추천합니다."
        )
        self.suggest_btn.clicked.connect(self._on_suggest)
        self.save_btn = QPushButton("설명 저장")
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.clicked.connect(self._on_save)

        actions = QHBoxLayout()
        actions.addWidget(self.pages_label)
        actions.addStretch(1)
        actions.addWidget(self.suggest_btn)
        actions.addWidget(self.save_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.addLayout(top)
        layout.addWidget(self.meta)
        layout.addWidget(QLabel("설명"))
        layout.addWidget(self.desc_edit)
        layout.addLayout(actions)

        self.set_repository(None)

    def set_repository(self, repo: Repository | None) -> None:
        self._repo = repo
        enabled = repo is not None
        self.desc_edit.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        self.suggest_btn.setEnabled(enabled)
        self.visibility_btn.setEnabled(enabled)
        self.open_repo_btn.setEnabled(enabled)

        if repo is None:
            self.title.setText("저장소를 선택하세요")
            self.meta.setText("왼쪽 또는 오른쪽 목록에서 항목을 선택하면 상세 정보가 표시됩니다.")
            self.desc_edit.clear()
            self.visibility_btn.setText("공개 여부")
            self.visibility_btn.setChecked(False)
            self.pages_label.setText("GitHub Pages: 없음")
            self.pages_btn.setEnabled(False)
            return

        self.title.setText(repo.full_name)
        self.meta.setText(
            f"생성일 {repo.format_created()}  ·  마지막 업데이트 {repo.format_updated()}"
            f"  ·  {'아카이브됨' if repo.archived else '활성'}"
        )
        self.desc_edit.setPlainText(repo.description or "")
        self.visibility_btn.blockSignals(True)
        self.visibility_btn.setChecked(not repo.private)
        self.visibility_btn.setText("공개" if not repo.private else "비공개")
        self.visibility_btn.blockSignals(False)

        if repo.has_pages:
            self.pages_label.setText(f"GitHub Pages: {repo.pages_url or '있음'}")
            self.pages_btn.setEnabled(True)
        else:
            self.pages_label.setText("GitHub Pages: 없음")
            self.pages_btn.setEnabled(False)

    def apply_suggestion(self, text: str) -> None:
        self.desc_edit.setPlainText(text)

    def _on_save(self) -> None:
        if self._repo is None:
            return
        self.save_description_requested.emit(self._repo, self.desc_edit.toPlainText().strip())

    def _on_suggest(self) -> None:
        if self._repo is None:
            return
        self.suggest_description_requested.emit(self._repo)

    def _on_visibility_clicked(self) -> None:
        if self._repo is None:
            return
        # Revert visual until API succeeds; main window will refresh
        self.visibility_btn.blockSignals(True)
        self.visibility_btn.setChecked(not self._repo.private)
        self.visibility_btn.setText("공개" if not self._repo.private else "비공개")
        self.visibility_btn.blockSignals(False)
        self.toggle_visibility_requested.emit(self._repo)

    def _open_repo(self) -> None:
        if self._repo is not None:
            QDesktopServices.openUrl(QUrl(self._repo.html_url))

    def _open_pages(self) -> None:
        if self._repo is None:
            return
        url = self._repo.pages_url
        if url:
            QDesktopServices.openUrl(QUrl(url))
