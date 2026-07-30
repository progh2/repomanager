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

from repomanager.i18n import tr
from repomanager.models.repository import Repository


class RepoDetailPanel(QFrame):
    save_description_requested = Signal(object, str)
    toggle_visibility_requested = Signal(object)
    suggest_description_requested = Signal(object)
    rename_requested = Signal(object)
    backup_requested = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("detailPane")
        self._repo: Repository | None = None

        self.title = QLabel()
        self.title.setObjectName("paneTitle")
        self.meta = QLabel()
        self.meta.setObjectName("hintLabel")
        self.meta.setWordWrap(True)

        self.visibility_btn = QPushButton()
        self.visibility_btn.setObjectName("visibilitySwitch")
        self.visibility_btn.setCursor(QtCursorPointing())
        self.visibility_btn.clicked.connect(self._on_visibility_clicked)

        self.pages_label = QLabel()
        self.pages_btn = QPushButton()
        self.pages_btn.setObjectName("pagesBtn")
        self.pages_btn.clicked.connect(self._open_pages)

        self.open_repo_btn = QPushButton()
        self.open_repo_btn.setObjectName("secondaryBtn")
        self.open_repo_btn.clicked.connect(self._open_repo)

        self.rename_btn = QPushButton()
        self.rename_btn.clicked.connect(self._on_rename)

        self.backup_btn = QPushButton()
        self.backup_btn.clicked.connect(self._on_backup)

        top = QHBoxLayout()
        top.addWidget(self.title, stretch=1)
        top.addWidget(self.visibility_btn)
        top.addWidget(self.rename_btn)
        top.addWidget(self.backup_btn)
        top.addWidget(self.open_repo_btn)
        top.addWidget(self.pages_btn)

        self.desc_label = QLabel()
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(90)

        self.suggest_btn = QPushButton()
        self.suggest_btn.clicked.connect(self._on_suggest)
        self.save_btn = QPushButton()
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
        layout.addWidget(self.desc_label)
        layout.addWidget(self.desc_edit)
        layout.addLayout(actions)

        self.retranslate_ui()
        self.set_repository(None)

    def retranslate_ui(self) -> None:
        self.open_repo_btn.setText(tr("detail.open_repo"))
        self.pages_btn.setText(tr("detail.pages_open"))
        self.rename_btn.setText(tr("detail.rename"))
        self.rename_btn.setToolTip(tr("detail.rename_tip"))
        self.backup_btn.setText(tr("detail.backup"))
        self.backup_btn.setToolTip(tr("detail.backup_tip"))
        self.desc_label.setText(tr("detail.desc_label"))
        self.desc_edit.setPlaceholderText(tr("detail.desc_placeholder"))
        self.suggest_btn.setText(tr("detail.suggest"))
        self.suggest_btn.setToolTip(tr("detail.suggest_tip"))
        self.save_btn.setText(tr("detail.save"))
        self.set_repository(self._repo)

    def set_repository(self, repo: Repository | None) -> None:
        self._repo = repo
        enabled = repo is not None
        self.desc_edit.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        self.suggest_btn.setEnabled(enabled)
        self.visibility_btn.setEnabled(enabled)
        self.open_repo_btn.setEnabled(enabled)
        self.rename_btn.setEnabled(enabled and not (repo.archived if repo else True))
        self.backup_btn.setEnabled(enabled)

        if repo is None:
            self.title.setText(tr("detail.select"))
            self.meta.setText(tr("detail.select_hint"))
            self.desc_edit.clear()
            self.visibility_btn.setText(tr("vis.none"))
            self.visibility_btn.setProperty("publicState", "")
            self.visibility_btn.style().unpolish(self.visibility_btn)
            self.visibility_btn.style().polish(self.visibility_btn)
            self.pages_label.setText(tr("detail.pages_none"))
            self.pages_btn.setEnabled(False)
            self.pages_btn.setProperty("pagesAvailable", False)
            self.pages_btn.setToolTip(tr("detail.pages_tip_off"))
            self._refresh_btn_style(self.pages_btn)
            return

        icons = []
        if repo.has_pages:
            icons.append("⌂")
        if repo.fork:
            icons.append("⑂")
        prefix = (" ".join(icons) + "  ") if icons else ""
        self.title.setText(f"{prefix}{repo.full_name}")
        state = tr("detail.state_archived") if repo.archived else tr("detail.state_active")
        self.meta.setText(
            tr(
                "detail.meta",
                created=repo.format_created(),
                updated=repo.format_updated(),
                state=state,
            )
        )
        self.desc_edit.setPlainText(repo.description or "")
        if repo.private:
            self.visibility_btn.setText(tr("vis.click_to_public"))
            self.visibility_btn.setProperty("publicState", "private")
        else:
            self.visibility_btn.setText(tr("vis.click_to_private"))
            self.visibility_btn.setProperty("publicState", "public")
        self._refresh_btn_style(self.visibility_btn)

        if repo.has_pages:
            self.pages_label.setText(tr("detail.pages_yes", url=repo.pages_url or "yes"))
            self.pages_btn.setEnabled(True)
            self.pages_btn.setProperty("pagesAvailable", True)
            self.pages_btn.setToolTip(tr("detail.pages_tip_on"))
        else:
            self.pages_label.setText(tr("detail.pages_none"))
            self.pages_btn.setEnabled(False)
            self.pages_btn.setProperty("pagesAvailable", False)
            self.pages_btn.setToolTip(tr("detail.pages_tip_off"))
        self._refresh_btn_style(self.pages_btn)

    def apply_suggestion(self, text: str) -> None:
        self.desc_edit.setPlainText(text)

    @staticmethod
    def _refresh_btn_style(btn: QPushButton) -> None:
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        btn.update()

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
        self.toggle_visibility_requested.emit(self._repo)

    def _on_rename(self) -> None:
        if self._repo is None:
            return
        self.rename_requested.emit(self._repo)

    def _on_backup(self) -> None:
        if self._repo is None:
            return
        self.backup_requested.emit(self._repo)

    def _open_repo(self) -> None:
        if self._repo is not None:
            QDesktopServices.openUrl(QUrl(self._repo.html_url))

    def _open_pages(self) -> None:
        if self._repo is None or not self._repo.pages_url:
            return
        QDesktopServices.openUrl(QUrl(self._repo.pages_url))


def QtCursorPointing():
    from PySide6.QtCore import Qt

    return Qt.CursorShape.PointingHandCursor
