"""Confirmation dialog before archive/unarchive/delete."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from repomanager.i18n import tr
from repomanager.models.repository import Repository

DELETE_CONFIRM_WORD = "DELETE"


class ConfirmDialog(QDialog):
    def __init__(
        self,
        *,
        action: str,
        repositories: list[Repository],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._action = action.lower()
        self._is_delete = self._action == "delete"
        self._is_unarchive = self._action == "unarchive"
        if self._is_delete:
            title = tr("confirm.delete_title")
        elif self._is_unarchive:
            title = tr("confirm.unarchive_title")
        else:
            title = tr("confirm.archive_title")
        self.setWindowTitle(title)
        self.setMinimumWidth(520)
        self.setMinimumHeight(400)

        count = len(repositories)
        if self._is_delete:
            warning = tr("confirm.delete_warning", n=count)
        elif self._is_unarchive:
            warning = tr("confirm.unarchive_warning", n=count)
        else:
            warning = tr("confirm.archive_warning", n=count)

        label = QLabel(warning)
        label.setWordWrap(True)
        if self._is_delete:
            label.setStyleSheet("color: #b42318; font-weight: 600;")

        listing = QListWidget()
        listing.setAlternatingRowColors(True)
        for repo in repositories:
            text = f"{repo.full_name} — {repo.short_description}"
            item = QListWidgetItem(text)
            item.setToolTip(repo.description or tr("list.no_desc"))
            listing.addItem(item)

        self._confirm_input: QLineEdit | None = None
        confirm_hint: QLabel | None = None
        if self._is_delete:
            confirm_hint = QLabel(tr("confirm.delete_hint", word=DELETE_CONFIRM_WORD))
            confirm_hint.setWordWrap(True)
            self._confirm_input = QLineEdit()
            self._confirm_input.setPlaceholderText(DELETE_CONFIRM_WORD)
            self._confirm_input.textChanged.connect(self._update_accept_enabled)

        self._buttons = QDialogButtonBox()
        if self._is_delete:
            accept_text = tr("confirm.delete_accept")
        elif self._is_unarchive:
            accept_text = tr("confirm.unarchive_accept")
        else:
            accept_text = tr("confirm.archive_accept")
        self._accept_btn = self._buttons.addButton(
            accept_text,
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        self._buttons.addButton(tr("confirm.cancel"), QDialogButtonBox.ButtonRole.RejectRole)
        self._accept_btn.setDefault(False)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(listing)
        if confirm_hint is not None and self._confirm_input is not None:
            layout.addWidget(confirm_hint)
            layout.addWidget(self._confirm_input)
        layout.addWidget(self._buttons)

        self._update_accept_enabled()

    def _update_accept_enabled(self) -> None:
        if self._confirm_input is None:
            self._accept_btn.setEnabled(True)
            return
        enabled = self._confirm_input.text().strip() == DELETE_CONFIRM_WORD
        self._accept_btn.setEnabled(enabled)
