"""Confirmation dialog before archive/delete."""

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
        self.setWindowTitle("삭제 확인" if self._is_delete else "아카이브 확인")
        self.setMinimumWidth(520)
        self.setMinimumHeight(400)

        if self._is_delete:
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
        if self._is_delete:
            label.setStyleSheet("color: #b00020; font-weight: 600;")

        listing = QListWidget()
        for repo in repositories:
            text = f"{repo.full_name} — {repo.short_description}"
            item = QListWidgetItem(text)
            item.setToolTip(repo.description or "(설명 없음)")
            listing.addItem(item)

        self._confirm_input: QLineEdit | None = None
        confirm_hint: QLabel | None = None
        if self._is_delete:
            confirm_hint = QLabel(
                f'계속하려면 아래에 <b>{DELETE_CONFIRM_WORD}</b> 를 입력하세요.<br>'
                "삭제에는 <b>delete_repo</b> 권한이 필요합니다. "
                "권한이 없으면 도움말 → 삭제 권한 안내를 보세요."
            )
            confirm_hint.setWordWrap(True)
            self._confirm_input = QLineEdit()
            self._confirm_input.setPlaceholderText(DELETE_CONFIRM_WORD)
            self._confirm_input.textChanged.connect(self._update_accept_enabled)

        self._buttons = QDialogButtonBox()
        self._accept_btn = self._buttons.addButton(
            "영구 삭제" if self._is_delete else "아카이브",
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        self._buttons.addButton("취소", QDialogButtonBox.ButtonRole.RejectRole)
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
