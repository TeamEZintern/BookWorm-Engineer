"""Small circular busy indicator for inline loading states."""

from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import QWidget


class BusyIndicator(QWidget):
    """Animated circular spinner, hidden until ``start()`` is called."""

    SPIN_INTERVAL_MS = 50
    ARC_SPAN_DEGREES = 90

    def __init__(self, color: str = "#888888", parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self.setFixedSize(16, 16)
        self.setVisible(False)

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def start(self) -> None:
        if not self._timer.isActive():
            self._timer.start(self.SPIN_INTERVAL_MS)
        self.setVisible(True)
        self.update()

    def stop(self) -> None:
        self._timer.stop()
        self.setVisible(False)

    def _rotate(self) -> None:
        self._angle = (self._angle + 30) % 360
        self.update()

    def paintEvent(self, _event) -> None:
        if not self.isVisible():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        side = min(self.width(), self.height())
        margin = 2
        rect = QRect(margin, margin, side - 2 * margin, side - 2 * margin)

        pen = QPen(self._color)
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(
            rect,
            self._angle * 16,
            self.ARC_SPAN_DEGREES * 16,
        )
