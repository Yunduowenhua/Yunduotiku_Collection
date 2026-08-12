from PySide6.QtWidgets import QLabel, QRubberBand
from PySide6.QtCore import Qt, Signal, QRect, QPoint
from PySide6.QtGui import QMouseEvent, QPainter, QPen, QColor

class CropperLabel(QLabel):
    crop_requested = Signal(QRect)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
        self.is_cropping = False
        self.setStyleSheet("""
            QRubberBand {
                border: 2px solid #06b6d4;
                background-color: rgba(6, 182, 212, 0.25);
            }
        """)

    def enable_cropping(self, enable: bool):
        self.is_cropping = enable
        if not enable:
            self.rubber_band.hide()
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.CrossCursor)

    def mousePressEvent(self, event: QMouseEvent):
        if self.is_cropping and event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.rubber_band.setGeometry(QRect(self.origin, self.origin))
            self.rubber_band.show()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_cropping and not self.origin.isNull():
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.is_cropping and event.button() == Qt.LeftButton:
            rect = self.rubber_band.geometry()
            self.rubber_band.hide()
            self.origin = QPoint()
            if rect.width() > 10 and rect.height() > 10:
                self.crop_requested.emit(rect)
            self.enable_cropping(False)
        super().mouseReleaseEvent(event)
