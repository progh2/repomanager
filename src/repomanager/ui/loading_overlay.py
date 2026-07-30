"""Semi-transparent busy overlay with a spinning arc and status text."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class LoadingOverlay(QWidget):
    """Covers its parent widget while a long operation runs."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._angle = 0
        self._text = ""
        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._advance)
        parent.installEventFilter(self)
        self.hide()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        if obj is self.parent() and event.type() in (
            QEvent.Type.Resize,
            QEvent.Type.Show,
        ):
            self.setGeometry(self.parent().rect())
        return False

    def start(self, text: str) -> None:
        self._text = text
        self.setGeometry(self.parent().rect())
        self.raise_()
        self.show()
        self._timer.start()

    def set_text(self, text: str) -> None:
        self._text = text
        if self.isVisible():
            self.update()

    def stop(self) -> None:
        self._timer.stop()
        self.hide()

    def _advance(self) -> None:
        self._angle = (self._angle + 8) % 360
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(238, 242, 245, 215))

        center = self.rect().center()
        radius = 26
        spinner_rect = QRectF(
            center.x() - radius,
            center.y() - radius - 18,
            radius * 2,
            radius * 2,
        )

        track_pen = QPen(QColor(13, 122, 111, 45), 5)
        painter.setPen(track_pen)
        painter.drawEllipse(spinner_rect)

        arc_pen = QPen(QColor("#0d7a6f"), 5)
        arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(arc_pen)
        painter.drawArc(spinner_rect, -self._angle * 16, 100 * 16)

        if self._text:
            painter.setPen(QColor("#14353a"))
            font = painter.font()
            font.setPointSize(11)
            font.setBold(True)
            painter.setFont(font)
            text_rect = self.rect().adjusted(
                20, int(spinner_rect.bottom()) + 12, -20, 0
            )
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                self._text,
            )
        painter.end()
