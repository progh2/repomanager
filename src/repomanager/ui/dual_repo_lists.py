"""Dual-pane Active / Archive repository lists with transfer arrows."""

from __future__ import annotations

from PySide6.QtCore import Qt, QSize, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from repomanager.models.repository import Repository

OWNER_ALL = "모든 소유자"
VIS_ALL = "모든 공개범위"
VIS_PUBLIC = "공개"
VIS_PRIVATE = "비공개"


class DualRepoLists(QWidget):
    selection_changed = Signal(int)
    current_repo_changed = Signal(object)  # Repository | None
    archive_requested = Signal(list)  # list[Repository]
    unarchive_requested = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._all_repos: list[Repository] = []
        self.setObjectName("dualRoot")

        self.search = QLineEdit()
        self.search.setPlaceholderText("이름 또는 설명 검색...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._rebuild_lists)

        self.owner_filter = QComboBox()
        self.owner_filter.addItem(OWNER_ALL)
        self.owner_filter.currentIndexChanged.connect(self._rebuild_lists)

        self.visibility_filter = QComboBox()
        self.visibility_filter.addItems([VIS_ALL, VIS_PUBLIC, VIS_PRIVATE])
        self.visibility_filter.currentIndexChanged.connect(self._rebuild_lists)

        filters = QHBoxLayout()
        filters.setSpacing(10)
        filters.addWidget(self.search, stretch=1)
        filters.addWidget(self.owner_filter)
        filters.addWidget(self.visibility_filter)

        self.active_title = QLabel("활성 (Active)")
        self.active_title.setObjectName("paneTitle")
        self.active_count = QLabel("0")
        self.active_count.setObjectName("paneCount")
        active_header = QHBoxLayout()
        active_header.addWidget(self.active_title)
        active_header.addStretch(1)
        active_header.addWidget(self.active_count)

        self.archive_title = QLabel("아카이브 (Archive)")
        self.archive_title.setObjectName("paneTitle")
        self.archive_count = QLabel("0")
        self.archive_count.setObjectName("paneCount")
        archive_header = QHBoxLayout()
        archive_header.addWidget(self.archive_title)
        archive_header.addStretch(1)
        archive_header.addWidget(self.archive_count)

        self.active_list = self._make_list()
        self.archive_list = self._make_list()
        self.active_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.archive_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.active_list.itemDoubleClicked.connect(self._open_item)
        self.archive_list.itemDoubleClicked.connect(self._open_item)

        self.to_archive_btn = QPushButton("→")
        self.to_archive_btn.setObjectName("transferBtn")
        self.to_archive_btn.setToolTip("선택한 활성 저장소를 아카이브로 이동")
        self.to_archive_btn.clicked.connect(self._emit_archive)
        self.to_active_btn = QPushButton("←")
        self.to_active_btn.setObjectName("transferBtn")
        self.to_active_btn.setToolTip("선택한 아카이브 저장소를 활성으로 복원")
        self.to_active_btn.clicked.connect(self._emit_unarchive)

        self.open_btn = QPushButton("GitHub에서 열기")
        self.open_btn.setObjectName("secondaryBtn")
        self.open_btn.clicked.connect(self._open_selected)

        transfer = QVBoxLayout()
        transfer.setSpacing(12)
        transfer.addStretch(1)
        transfer.addWidget(self.to_archive_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        transfer.addWidget(self.to_active_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        transfer.addSpacing(16)
        transfer.addWidget(self.open_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        transfer.addStretch(1)

        active_pane = QFrame()
        active_pane.setObjectName("listPane")
        active_layout = QVBoxLayout(active_pane)
        active_layout.setContentsMargins(12, 12, 12, 12)
        active_layout.setSpacing(8)
        active_layout.addLayout(active_header)
        active_layout.addWidget(self.active_list)

        archive_pane = QFrame()
        archive_pane.setObjectName("listPane")
        archive_layout = QVBoxLayout(archive_pane)
        archive_layout.setContentsMargins(12, 12, 12, 12)
        archive_layout.setSpacing(8)
        archive_layout.addLayout(archive_header)
        archive_layout.addWidget(self.archive_list)

        lists_row = QHBoxLayout()
        lists_row.setSpacing(12)
        lists_row.addWidget(active_pane, stretch=1)
        lists_row.addLayout(transfer)
        lists_row.addWidget(archive_pane, stretch=1)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)
        root.addLayout(filters)
        root.addLayout(lists_row, stretch=1)

        self._update_transfer_buttons()

    def _make_list(self) -> QListWidget:
        widget = QListWidget()
        widget.setObjectName("repoList")
        widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        widget.setAlternatingRowColors(True)
        widget.setUniformItemSizes(False)
        widget.setSpacing(4)
        return widget

    def set_repositories(self, repos: list[Repository]) -> None:
        self._all_repos = list(repos)
        self._rebuild_owner_filter()
        self._rebuild_lists()

    def upsert_repository(self, repo: Repository) -> None:
        """Replace one repo in the local cache and refresh lists."""
        updated: list[Repository] = []
        found = False
        for existing in self._all_repos:
            if existing.full_name == repo.full_name:
                updated.append(repo)
                found = True
            else:
                updated.append(existing)
        if not found:
            updated.append(repo)
        self._all_repos = updated
        self._rebuild_lists()

    def selected_repositories(self) -> list[Repository]:
        return self._selected_from(self.active_list) + self._selected_from(self.archive_list)

    def selected_active(self) -> list[Repository]:
        return self._selected_from(self.active_list)

    def selected_archived(self) -> list[Repository]:
        return self._selected_from(self.archive_list)

    def select_all_visible(self) -> None:
        focus = self.focusWidget()
        target = self.archive_list if focus is self.archive_list else self.active_list
        target.selectAll()
        self._on_selection_changed()

    def clear_selection(self) -> None:
        self.active_list.clearSelection()
        self.archive_list.clearSelection()
        self._on_selection_changed()

    def _rebuild_owner_filter(self) -> None:
        current = self.owner_filter.currentText()
        owners = sorted({repo.owner for repo in self._all_repos}, key=str.lower)
        self.owner_filter.blockSignals(True)
        self.owner_filter.clear()
        self.owner_filter.addItem(OWNER_ALL)
        self.owner_filter.addItems(owners)
        index = self.owner_filter.findText(current)
        self.owner_filter.setCurrentIndex(index if index >= 0 else 0)
        self.owner_filter.blockSignals(False)

    def _filtered(self) -> list[Repository]:
        query = self.search.text().strip().lower()
        owner = self.owner_filter.currentText()
        visibility = self.visibility_filter.currentText()
        result: list[Repository] = []
        for repo in self._all_repos:
            if owner != OWNER_ALL and repo.owner != owner:
                continue
            if visibility == VIS_PUBLIC and repo.private:
                continue
            if visibility == VIS_PRIVATE and not repo.private:
                continue
            if query:
                haystack = f"{repo.full_name} {repo.description}".lower()
                if query not in haystack:
                    continue
            result.append(repo)
        return result

    def _rebuild_lists(self) -> None:
        active_selected = {r.full_name for r in self.selected_active()}
        archive_selected = {r.full_name for r in self.selected_archived()}

        self.active_list.clear()
        self.archive_list.clear()

        active_count = 0
        archive_count = 0
        for repo in self._filtered():
            item = self._make_item(repo)
            if repo.archived:
                self.archive_list.addItem(item)
                archive_count += 1
                if repo.full_name in archive_selected:
                    item.setSelected(True)
            else:
                self.active_list.addItem(item)
                active_count += 1
                if repo.full_name in active_selected:
                    item.setSelected(True)

        self.active_count.setText(str(active_count))
        self.archive_count.setText(str(archive_count))
        self._on_selection_changed()

    def _make_item(self, repo: Repository) -> QListWidgetItem:
        visibility = "비공개" if repo.private else "공개"
        pages = " · Pages" if repo.has_pages else ""
        text = (
            f"{repo.full_name}\n"
            f"{visibility}{pages} · 생성 {repo.format_created()} · 업데이트 {repo.format_updated()}\n"
            f"{repo.short_description}"
        )
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, repo)
        tip = (
            f"{repo.html_url}\n"
            f"생성: {repo.format_created()}\n"
            f"업데이트: {repo.format_updated()}\n"
            f"{repo.description or '(설명 없음)'}"
        )
        if repo.has_pages:
            tip += f"\nPages: {repo.pages_url}"
        item.setToolTip(tip)
        item.setSizeHint(QSize(220, 72))
        return item

    def _selected_from(self, widget: QListWidget) -> list[Repository]:
        repos: list[Repository] = []
        for item in widget.selectedItems():
            repo = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(repo, Repository):
                repos.append(repo)
        return repos

    def _on_selection_changed(self) -> None:
        # Keep selections mutually exclusive between panes for clearer transfers
        if self.active_list.selectedItems() and self.archive_list.selectedItems():
            sender = self.sender()
            if sender is self.active_list:
                self.archive_list.blockSignals(True)
                self.archive_list.clearSelection()
                self.archive_list.blockSignals(False)
            elif sender is self.archive_list:
                self.active_list.blockSignals(True)
                self.active_list.clearSelection()
                self.active_list.blockSignals(False)
        count = len(self.selected_repositories())
        self.selection_changed.emit(count)
        selected = self.selected_repositories()
        current = selected[0] if len(selected) == 1 else None
        self.current_repo_changed.emit(current)
        self._update_transfer_buttons()

    def _update_transfer_buttons(self) -> None:
        self.to_archive_btn.setEnabled(bool(self.selected_active()))
        self.to_active_btn.setEnabled(bool(self.selected_archived()))
        self.open_btn.setEnabled(bool(self.selected_repositories()))

    def _emit_archive(self) -> None:
        selected = self.selected_active()
        if selected:
            self.archive_requested.emit(selected)

    def _emit_unarchive(self) -> None:
        selected = self.selected_archived()
        if selected:
            self.unarchive_requested.emit(selected)

    def _open_item(self, item: QListWidgetItem) -> None:
        repo = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(repo, Repository):
            QDesktopServices.openUrl(QUrl(repo.html_url))

    def _open_selected(self) -> None:
        selected = self.selected_repositories()
        if not selected:
            return
        QDesktopServices.openUrl(QUrl(selected[0].html_url))
