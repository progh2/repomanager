"""Confirmation dialog before archive/delete."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from repomanager.models.repository import Repository


class ConfirmDialog(QDialog):
    def __init__(
        self,
        *,
        action: str,
        repositories: list[Repository],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Confirm {action}")
        self.setMinimumWidth(520)
        self.setMinimumHeight(360)

        is_delete = action.lower() == "delete"
        if is_delete:
            warning = (
                f"선택한 {len(repositories)}개 저장소를 삭제합니다.\n"
                "이 작업은 되돌릴 수 없습니다."
            )
        else:
            warning = (
                f"선택한 {len(repositories)}개 저장소를 아카이브합니다.\n"
                "읽기 전용으로 보관되며, 나중에 GitHub에서 unarchive할 수 있습니다."
            )

        label = QLabel(warning)
        label.setWordWrap(True)
        if is_delete:
            label.setStyleSheet("color: #b00020; font-weight: 600;")

        listing = QListWidget()
        for repo in repositories:
            text = f"{repo.full_name} — {repo.short_description}"
            item = QListWidgetItem(text)
            item.setToolTip(repo.description or "(설명 없음)")
            listing.addItem(item)

        buttons = QDialogButtonBox()
        accept = buttons.addButton(
            "영구 삭제" if is_delete else "아카이브",
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        accept.setDefault(False)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(listing)
        layout.addWidget(buttons)
