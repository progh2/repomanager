"""List item delegate: icons + colored visibility badges."""

from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionViewItem

from repomanager.i18n import tr
from repomanager.models.repository import Repository
from repomanager.ui import theme


class RepoItemDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:  # noqa: ANN001
        painter.save()
        self.initStyleOption(option, index)
        option.widget.style().drawPrimitive(
            QStyle.PrimitiveElement.PE_PanelItemViewItem, option, painter, option.widget
        )

        repo = index.data(Qt.ItemDataRole.UserRole)
        if not isinstance(repo, Repository):
            painter.restore()
            return

        rect: QRect = option.rect.adjusted(10, 6, -10, -6)
        x, y, w = rect.x(), rect.y(), rect.width()

        icons = []
        if repo.has_pages:
            icons.append("⌂")
        if repo.fork:
            icons.append("⑂")
        icon_text = " ".join(icons)
        name = repo.full_name
        if icon_text:
            name = f"{icon_text}  {name}"

        name_font = QFont(option.font)
        name_font.setBold(True)
        painter.setFont(name_font)
        painter.setPen(QColor(theme.color("name")))
        painter.drawText(QRect(x, y, w, 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, name)

        vis = tr("vis.private") if repo.private else tr("vis.public")
        painter.setPen(
            QColor(theme.color("private")) if repo.private else QColor(theme.color("public"))
        )
        meta_font = QFont(option.font)
        meta_font.setPointSize(max(8, option.font.pointSize() - 1))
        meta_font.setBold(True)
        painter.setFont(meta_font)
        painter.drawText(
            QRect(x, y + 20, w, 16),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            f"{vis}  ·  {tr('list.created')} {repo.format_created()}  ·  {tr('list.updated')} {repo.format_updated()}",
        )

        painter.setPen(QColor(theme.color("muted")))
        desc_font = QFont(option.font)
        desc_font.setBold(False)
        desc_font.setPointSize(max(8, option.font.pointSize() - 1))
        painter.setFont(desc_font)
        painter.drawText(
            QRect(x, y + 38, w, 18),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            repo.short_description,
        )
        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:  # noqa: ANN001
        return QSize(option.rect.width(), 72)
