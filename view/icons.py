"""Runtime-painted application icon (no binary assets required)."""

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap


def app_icon(size: int = 256) -> QIcon:
    """Draw the StudyMate mark: a gradient tile with a white note card."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.TextAntialiasing, True)

    tile = QRectF(size * 0.06, size * 0.06, size * 0.88, size * 0.88)
    gradient = QLinearGradient(tile.topLeft(), tile.bottomRight())
    gradient.setColorAt(0.0, QColor("#6366f1"))
    gradient.setColorAt(1.0, QColor("#8b5cf6"))
    painter.setPen(Qt.NoPen)
    painter.setBrush(gradient)
    radius = size * 0.24
    painter.drawRoundedRect(tile, radius, radius)

    # Note card
    card = QRectF(size * 0.28, size * 0.24, size * 0.44, size * 0.52)
    painter.setBrush(QColor(255, 255, 255, 240))
    painter.drawRoundedRect(card, size * 0.055, size * 0.055)

    # Text lines
    pen = QPen(QColor("#6366f1"))
    pen.setWidthF(max(2.0, size * 0.035))
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    for index, offset in enumerate((0.36, 0.46, 0.56)):
        right = size * (0.62 if index < 2 else 0.52)
        painter.drawLine(
            int(size * 0.36),
            int(size * offset),
            int(right),
            int(size * offset),
        )
    painter.end()
    return QIcon(pixmap)
