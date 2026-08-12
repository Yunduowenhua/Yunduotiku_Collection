from PySide6.QtWidgets import QLabel, QRubberBand
from PySide6.QtCore import Qt, Signal, QRect, QPoint
from PySide6.QtGui import QMouseEvent

class CropperLabel(QLabel):
    crop_requested = Signal(QRect)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
        self.is_cropping = False
        self.setStyleSheet("""
            QRubberBand {
                border: 2px solid #f59e0b;
                background-color: rgba(245, 158, 11, 0.3);
            }
        """)

    def enable_cropping(self, enable: bool):
        self.is_cropping = enable
        if not enable:
            self.rubber_band.hide()
            self.setCursor(Qt.ArrowCursor)
            self.setStyleSheet("""
                background-color: #0b1326;
                border: 1px solid #334155;
                border-radius: 4px;
            """)
        else:
            self.setCursor(Qt.CrossCursor)
            self.setStyleSheet("""
                background-color: #0b1326;
                border: 3px solid #f59e0b;
                border-radius: 4px;
            """)

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
            
            # 只有当框选的区域宽度与高度均 > 10 像素时，才算作有效重划
            if rect.width() > 10 and rect.height() > 10:
                self.crop_requested.emit(rect)
                
            self.enable_cropping(False)
        super().mouseReleaseEvent(event)
