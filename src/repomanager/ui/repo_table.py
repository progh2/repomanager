"""Repository table widget with checkboxes and filters."""

from __future__ import annotations

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from repomanager.models.repository import Repository

COL_CHECK = 0
COL_NAME = 1
COL_VISIBILITY = 2
COL_DESCRIPTION = 3
COL_ARCHIVED = 4
COL_UPDATED = 5


class RepoTable(QWidget):
    selection_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._all_repos: list[Repository] = []
        self._visible_repos: list[Repository] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search name or description...")
        self.search.textChanged.connect(self._apply_filters)

        self.visibility_filter = QComboBox()
        self.visibility_filter.addItems(["All visibility", "Public", "Private"])
        self.visibility_filter.currentIndexChanged.connect(self._apply_filters)

        self.archived_filter = QComboBox()
        self.archived_filter.addItems(["All", "Active only", "Archived only"])
        self.archived_filter.currentIndexChanged.connect(self._apply_filters)

        filters = QHBoxLayout()
        filters.addWidget(self.search, stretch=1)
        filters.addWidget(self.visibility_filter)
        filters.addWidget(self.archived_filter)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["", "Repository", "Visibility", "Description", "Archived", "Updated"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(COL_CHECK, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_NAME, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_VISIBILITY, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_DESCRIPTION, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_ARCHIVED, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_UPDATED, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.cellDoubleClicked.connect(self._open_in_browser)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(filters)
        layout.addWidget(self.table)

    def set_repositories(self, repos: list[Repository]) -> None:
        self._all_repos = list(repos)
        self._apply_filters()

    def selected_repositories(self) -> list[Repository]:
        selected: list[Repository] = []
        for row, repo in enumerate(self._visible_repos):
            item = self.table.item(row, COL_CHECK)
            if item is not None and item.checkState() == Qt.CheckState.Checked:
                selected.append(repo)
        return selected

    def select_all_visible(self) -> None:
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            item = self.table.item(row, COL_CHECK)
            if item is not None:
                item.setCheckState(Qt.CheckState.Checked)
        self.table.blockSignals(False)
        self.selection_changed.emit(len(self.selected_repositories()))

    def clear_selection(self) -> None:
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            item = self.table.item(row, COL_CHECK)
            if item is not None:
                item.setCheckState(Qt.CheckState.Unchecked)
        self.table.blockSignals(False)
        self.selection_changed.emit(0)

    def _apply_filters(self) -> None:
        query = self.search.text().strip().lower()
        visibility = self.visibility_filter.currentText()
        archived_mode = self.archived_filter.currentText()

        filtered: list[Repository] = []
        for repo in self._all_repos:
            if visibility == "Public" and repo.private:
                continue
            if visibility == "Private" and not repo.private:
                continue
            if archived_mode == "Active only" and repo.archived:
                continue
            if archived_mode == "Archived only" and not repo.archived:
                continue
            if query:
                haystack = f"{repo.full_name} {repo.description}".lower()
                if query not in haystack:
                    continue
            filtered.append(repo)

        self._visible_repos = filtered
        self._rebuild_table()

    def _rebuild_table(self) -> None:
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.table.setRowCount(len(self._visible_repos))
        for row, repo in enumerate(self._visible_repos):
            check = QTableWidgetItem()
            check.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            check.setCheckState(Qt.CheckState.Unchecked)
            self.table.setItem(row, COL_CHECK, check)

            name_item = QTableWidgetItem(repo.full_name)
            name_item.setData(Qt.ItemDataRole.UserRole, repo.html_url)
            name_item.setToolTip(repo.html_url)
            self.table.setItem(row, COL_NAME, name_item)

            vis_item = QTableWidgetItem(repo.visibility)
            self.table.setItem(row, COL_VISIBILITY, vis_item)

            desc_item = QTableWidgetItem(repo.short_description)
            desc_item.setToolTip(repo.description or "(설명 없음)")
            self.table.setItem(row, COL_DESCRIPTION, desc_item)

            arch_item = QTableWidgetItem("Yes" if repo.archived else "No")
            self.table.setItem(row, COL_ARCHIVED, arch_item)

            updated = (
                repo.updated_at.strftime("%Y-%m-%d %H:%M") if repo.updated_at else "-"
            )
            self.table.setItem(row, COL_UPDATED, QTableWidgetItem(updated))

        self.table.blockSignals(False)
        self.selection_changed.emit(0)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() == COL_CHECK:
            self.selection_changed.emit(len(self.selected_repositories()))

    def _open_in_browser(self, row: int, _column: int) -> None:
        if 0 <= row < len(self._visible_repos):
            QDesktopServices.openUrl(QUrl(self._visible_repos[row].html_url))
