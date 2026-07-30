"""Tests for the rename confirmation dialog."""

from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtWidgets import QApplication

from repomanager.i18n import set_language
from repomanager.models.repository import Repository
from repomanager.ui.rename_dialog import RENAME_CONFIRM_WORD, RenameDialog


def _repo() -> Repository:
    return Repository(
        owner="alice",
        name="old-name",
        description="",
        private=False,
        html_url="https://github.com/alice/old-name",
        archived=False,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        has_pages=False,
        pages_url="",
    )


def test_rename_dialog_requires_word_and_new_name() -> None:
    app = QApplication.instance() or QApplication([])
    assert app is not None
    set_language("en", notify=False)
    dialog = RenameDialog(_repo())
    assert not dialog._accept_btn.isEnabled()

    dialog.new_name.setText("new-name")
    assert not dialog._accept_btn.isEnabled()

    dialog.confirm_input.setText(RENAME_CONFIRM_WORD)
    assert dialog._accept_btn.isEnabled()
    assert dialog.new_repository_name() == "new-name"

    dialog.new_name.setText("bad name!")
    assert not dialog._accept_btn.isEnabled()
