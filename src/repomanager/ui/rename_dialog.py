"""Confirm dialog for renaming a repository (requires typing RENAME)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from repomanager.i18n import tr
from repomanager.models.repository import Repository

RENAME_CONFIRM_WORD = "RENAME"


class RenameDialog(QDialog):
    def __init__(self, repository: Repository, parent=None) -> None:
        super().__init__(parent)
        self._repo = repository
        self.setWindowTitle(tr("rename.title"))
        self.setMinimumWidth(520)

        warning = QLabel(tr("rename.warning", name=repository.full_name))
        warning.setWordWrap(True)
        warning.setStyleSheet("color: #b42318; font-weight: 600;")

        links = QLabel(tr("rename.links_note"))
        links.setWordWrap(True)

        self.current_label = QLabel(repository.name)
        self.new_name = QLineEdit()
        self.new_name.setText(repository.name)
        self.new_name.setPlaceholderText(tr("rename.new_placeholder"))
        self.new_name.textChanged.connect(self._update_accept_enabled)

        form = QFormLayout()
        form.addRow(tr("rename.current"), self.current_label)
        form.addRow(tr("rename.new"), self.new_name)

        confirm_hint = QLabel(tr("rename.confirm_hint", word=RENAME_CONFIRM_WORD))
        confirm_hint.setWordWrap(True)
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText(RENAME_CONFIRM_WORD)
        self.confirm_input.textChanged.connect(self._update_accept_enabled)

        self._buttons = QDialogButtonBox()
        self._accept_btn = self._buttons.addButton(
            tr("rename.accept"), QDialogButtonBox.ButtonRole.AcceptRole
        )
        self._buttons.addButton(tr("confirm.cancel"), QDialogButtonBox.ButtonRole.RejectRole)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(warning)
        layout.addWidget(links)
        layout.addLayout(form)
        layout.addWidget(confirm_hint)
        layout.addWidget(self.confirm_input)
        layout.addWidget(self._buttons)

        self._update_accept_enabled()

    def new_repository_name(self) -> str:
        return self.new_name.text().strip()

    def _update_accept_enabled(self) -> None:
        proposed = self.new_name.text().strip()
        typed = self.confirm_input.text().strip() == RENAME_CONFIRM_WORD
        changed = bool(proposed) and proposed != self._repo.name
        # GitHub repo names: letters, numbers, ., -, _
        valid_chars = all(c.isalnum() or c in "._-" for c in proposed) if proposed else False
        self._accept_btn.setEnabled(typed and changed and valid_chars)
