"""Dual-pane Active / Archive repository lists with transfer arrows."""

from __future__ import annotations

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
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

from repomanager.config import app_settings
from repomanager.i18n import tr
from repomanager.models.repository import Repository
from repomanager.ui.repo_item_delegate import RepoItemDelegate


SORT_MODES = ("updated_desc", "updated_asc", "created_desc", "created_asc", "name")

KEY_VIS = "filters/visibility"
KEY_PAGES = "filters/pages"
KEY_FORK = "filters/fork"
KEY_SORT = "filters/sort"
KEY_OWNER = "filters/owner"


def _to_index(value: object) -> int:
    try:
        return max(0, int(value))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


class DualRepoLists(QWidget):
    selection_changed = Signal(int)
    current_repo_changed = Signal(object)  # Repository | None
    archive_requested = Signal(list)
    unarchive_requested = Signal(list)
    delete_requested = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._all_repos: list[Repository] = []
        self.setObjectName("dualRoot")
        self._delegate = RepoItemDelegate(self)

        self.search = QLineEdit()
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._rebuild_lists)

        self.owner_filter = QComboBox()
        self.owner_filter.currentIndexChanged.connect(self._rebuild_lists)

        self.visibility_filter = QComboBox()
        self.visibility_filter.currentIndexChanged.connect(self._rebuild_lists)

        self.pages_filter = QComboBox()
        self.pages_filter.currentIndexChanged.connect(self._rebuild_lists)

        self.fork_filter = QComboBox()
        self.fork_filter.currentIndexChanged.connect(self._rebuild_lists)

        self.sort_combo = QComboBox()
        self.sort_combo.currentIndexChanged.connect(self._rebuild_lists)

        filters = QHBoxLayout()
        filters.setSpacing(10)
        filters.addWidget(self.search, stretch=1)
        filters.addWidget(self.owner_filter)
        filters.addWidget(self.visibility_filter)
        filters.addWidget(self.pages_filter)
        filters.addWidget(self.fork_filter)
        filters.addWidget(self.sort_combo)

        self.active_title = QLabel()
        self.active_title.setObjectName("paneTitle")
        self.active_count = QLabel("0")
        self.active_count.setObjectName("paneCount")
        active_header = QHBoxLayout()
        active_header.addWidget(self.active_title)
        active_header.addStretch(1)
        active_header.addWidget(self.active_count)

        self.archive_title = QLabel()
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
        self.to_archive_btn.clicked.connect(self._emit_archive)
        self.to_active_btn = QPushButton("←")
        self.to_active_btn.setObjectName("transferBtn")
        self.to_active_btn.clicked.connect(self._emit_unarchive)

        transfer = QVBoxLayout()
        transfer.setSpacing(12)
        transfer.addStretch(1)
        transfer.addWidget(self.to_archive_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        transfer.addWidget(self.to_active_btn, alignment=Qt.AlignmentFlag.AlignCenter)
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

        for lst in (self.active_list, self.archive_list):
            shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), lst)
            shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
            shortcut.activated.connect(self._emit_delete)

        self._pending_owner = ""
        self._state_ready = False
        self.retranslate_ui()
        self._restore_state()
        self._update_transfer_buttons()

    def retranslate_ui(self) -> None:
        self.search.setPlaceholderText(tr("search.placeholder"))
        self.active_title.setText(tr("pane.active"))
        self.archive_title.setText(tr("pane.archive"))
        self.to_archive_btn.setToolTip(tr("tip.to_archive"))
        self.to_active_btn.setToolTip(tr("tip.to_active"))

        owner_current = self.owner_filter.currentText()
        owners = [self.owner_filter.itemText(i) for i in range(1, self.owner_filter.count())]
        self.owner_filter.blockSignals(True)
        self.owner_filter.clear()
        self.owner_filter.addItem(tr("filter.owner_all"))
        self.owner_filter.addItems(owners)
        idx = self.owner_filter.findText(owner_current)
        self.owner_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.owner_filter.blockSignals(False)

        vis_index = self.visibility_filter.currentIndex()
        self.visibility_filter.blockSignals(True)
        self.visibility_filter.clear()
        self.visibility_filter.addItems(
            [tr("filter.vis_all"), tr("filter.public"), tr("filter.private")]
        )
        self.visibility_filter.setCurrentIndex(max(0, vis_index))
        self.visibility_filter.blockSignals(False)

        pages_index = self.pages_filter.currentIndex()
        self.pages_filter.blockSignals(True)
        self.pages_filter.clear()
        self.pages_filter.addItems(
            [tr("filter.pages_all"), tr("filter.pages_yes"), tr("filter.pages_no")]
        )
        self.pages_filter.setCurrentIndex(max(0, pages_index))
        self.pages_filter.blockSignals(False)

        fork_index = self.fork_filter.currentIndex()
        self.fork_filter.blockSignals(True)
        self.fork_filter.clear()
        self.fork_filter.addItems(
            [tr("filter.fork_all"), tr("filter.fork_only"), tr("filter.fork_none")]
        )
        self.fork_filter.setCurrentIndex(max(0, fork_index))
        self.fork_filter.blockSignals(False)

        sort_current = self.sort_combo.currentData() or SORT_MODES[0]
        self.sort_combo.blockSignals(True)
        self.sort_combo.clear()
        for mode in SORT_MODES:
            self.sort_combo.addItem(tr(f"sort.{mode}"), mode)
        idx = self.sort_combo.findData(sort_current)
        self.sort_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.sort_combo.setToolTip(tr("sort.label"))
        self.sort_combo.blockSignals(False)
        self._rebuild_lists()

    def _make_list(self) -> QListWidget:
        widget = QListWidget()
        widget.setObjectName("repoList")
        widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        widget.setAlternatingRowColors(True)
        widget.setSpacing(4)
        widget.setItemDelegate(self._delegate)
        return widget

    def set_repositories(self, repos: list[Repository]) -> None:
        self._all_repos = list(repos)
        self._rebuild_owner_filter()
        self._rebuild_lists()

    def upsert_repository(self, repo: Repository) -> None:
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
        current = self._pending_owner or self.owner_filter.currentText()
        owners = sorted({repo.owner for repo in self._all_repos}, key=str.lower)
        self.owner_filter.blockSignals(True)
        self.owner_filter.clear()
        self.owner_filter.addItem(tr("filter.owner_all"))
        self.owner_filter.addItems(owners)
        index = self.owner_filter.findText(current)
        self.owner_filter.setCurrentIndex(index if index >= 0 else 0)
        self.owner_filter.blockSignals(False)
        if self._pending_owner and index >= 0:
            self._pending_owner = ""

    def _restore_state(self) -> None:
        settings = app_settings()
        for combo, key in (
            (self.visibility_filter, KEY_VIS),
            (self.pages_filter, KEY_PAGES),
            (self.fork_filter, KEY_FORK),
        ):
            index = _to_index(settings.value(key, 0))
            if 0 <= index < combo.count():
                combo.blockSignals(True)
                combo.setCurrentIndex(index)
                combo.blockSignals(False)
        sort_mode = str(settings.value(KEY_SORT, "") or "")
        idx = self.sort_combo.findData(sort_mode)
        if idx >= 0:
            self.sort_combo.blockSignals(True)
            self.sort_combo.setCurrentIndex(idx)
            self.sort_combo.blockSignals(False)
        self._pending_owner = str(settings.value(KEY_OWNER, "") or "")
        self._state_ready = True
        self._rebuild_lists()

    def _save_state(self) -> None:
        if not self._state_ready:
            return
        settings = app_settings()
        settings.setValue(KEY_VIS, self.visibility_filter.currentIndex())
        settings.setValue(KEY_PAGES, self.pages_filter.currentIndex())
        settings.setValue(KEY_FORK, self.fork_filter.currentIndex())
        settings.setValue(KEY_SORT, self.sort_combo.currentData() or "")
        owner = (
            self.owner_filter.currentText()
            if self.owner_filter.currentIndex() > 0
            else ""
        )
        settings.setValue(KEY_OWNER, owner)

    def _filtered(self) -> list[Repository]:
        query = self.search.text().strip().lower()
        owner = self.owner_filter.currentText()
        visibility = self.visibility_filter.currentText()
        result: list[Repository] = []
        for repo in self._all_repos:
            if owner != tr("filter.owner_all") and self.owner_filter.currentIndex() > 0:
                if repo.owner != owner:
                    continue
            if visibility == tr("filter.public") and repo.private:
                continue
            if visibility == tr("filter.private") and not repo.private:
                continue
            pages_mode = self.pages_filter.currentIndex()
            if pages_mode == 1 and not repo.has_pages:
                continue
            if pages_mode == 2 and repo.has_pages:
                continue
            fork_mode = self.fork_filter.currentIndex()
            if fork_mode == 1 and not repo.fork:
                continue
            if fork_mode == 2 and repo.fork:
                continue
            if query:
                haystack = f"{repo.full_name} {repo.description}".lower()
                if query not in haystack:
                    continue
            result.append(repo)
        return self._sorted(result)

    def _sorted(self, repos: list[Repository]) -> list[Repository]:
        mode = self.sort_combo.currentData() or SORT_MODES[0]

        def updated_ts(repo: Repository) -> float:
            return repo.updated_at.timestamp() if repo.updated_at else 0.0

        def created_ts(repo: Repository) -> float:
            return repo.created_at.timestamp() if repo.created_at else 0.0

        if mode == "name":
            return sorted(repos, key=lambda r: r.full_name.lower())
        if mode == "updated_asc":
            return sorted(repos, key=updated_ts)
        if mode == "created_desc":
            return sorted(repos, key=created_ts, reverse=True)
        if mode == "created_asc":
            return sorted(repos, key=created_ts)
        return sorted(repos, key=updated_ts, reverse=True)

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
        self._save_state()
        self._on_selection_changed()

    def _make_item(self, repo: Repository) -> QListWidgetItem:
        item = QListWidgetItem(repo.full_name)
        item.setData(Qt.ItemDataRole.UserRole, repo)
        tip_lines = [
            repo.html_url,
            f"{tr('list.created')}: {repo.format_created()}",
            f"{tr('list.updated')}: {repo.format_updated()}",
            repo.description or tr("list.no_desc"),
        ]
        if repo.has_pages:
            tip_lines.append(f"Pages: {repo.pages_url}")
        if repo.fork:
            tip_lines.append("fork")
        item.setToolTip("\n".join(tip_lines))
        return item

    def _selected_from(self, widget: QListWidget) -> list[Repository]:
        repos: list[Repository] = []
        for item in widget.selectedItems():
            repo = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(repo, Repository):
                repos.append(repo)
        return repos

    def _on_selection_changed(self) -> None:
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

    def _emit_archive(self) -> None:
        selected = self.selected_active()
        if selected:
            self.archive_requested.emit(selected)

    def _emit_unarchive(self) -> None:
        selected = self.selected_archived()
        if selected:
            self.unarchive_requested.emit(selected)

    def _emit_delete(self) -> None:
        selected = self.selected_repositories()
        if selected:
            self.delete_requested.emit(selected)

    def _open_item(self, item: QListWidgetItem) -> None:
        repo = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(repo, Repository):
            QDesktopServices.openUrl(QUrl(repo.html_url))
