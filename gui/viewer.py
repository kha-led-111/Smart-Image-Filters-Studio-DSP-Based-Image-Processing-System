"""
Image viewer, before/after comparison widget, and histogram canvas.
"""
import numpy as np
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy, QFrame
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QFont


class ImageViewer(QWidget):
    """Displays one or two images side by side (comparison mode)."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #0a0a14;")
        self._compare = False
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Original pane
        self._orig_pane = ImagePane("ORIGINAL")
        self._orig_pane.hide()
        layout.addWidget(self._orig_pane)

        # Processed pane
        self._proc_pane = ImagePane("PROCESSED")
        layout.addWidget(self._proc_pane)

    def set_compare_mode(self, enabled: bool):
        self._compare = enabled
        self._orig_pane.setVisible(enabled)

    def set_original(self, pixmap: QPixmap):
        self._orig_pane.set_image(pixmap)

    def set_processed(self, pixmap: QPixmap):
        self._proc_pane.set_image(pixmap)


class ImagePane(QWidget):
    def __init__(self, label_text: str):
        super().__init__()
        self.setStyleSheet("background: #0a0a14;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl = QLabel(label_text)
        lbl.setStyleSheet("font-size: 9px; letter-spacing: 2px; color: #556070;")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid #1a1a2e;")
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.image_label)

    def set_image(self, pixmap: QPixmap):
        self.image_label.setPixmap(
            pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            if not pixmap.isNull() else pixmap
        )
        self.image_label.setMinimumSize(200, 200)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        pix = self.image_label.pixmap()
        if pix and not pix.isNull():
            self.image_label.setPixmap(
                pix.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )


class CompareWidget(QWidget):
    """Placeholder — integrated into ImageViewer."""
    pass


class HistogramWidget(QWidget):
    """Custom histogram painter — RGB channels as line graphs."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #0d0d14; border: 1px solid #161628;")
        self._hist = None

    def update_histogram(self, hist: dict):
        self._hist = hist
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._hist:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        pad = 4

        # Background
        painter.fillRect(0, 0, W, H, QColor("#0d0d14"))

        channels = []
        if "r" in self._hist:
            channels = [
                (self._hist["b"], QColor(80, 144, 255, 180)),
                (self._hist["g"], QColor(80, 220, 120, 180)),
                (self._hist["r"], QColor(255, 80, 80, 180)),
            ]
        elif "gray" in self._hist:
            channels = [(self._hist["gray"], QColor(200, 200, 200, 200))]

        if not channels:
            return

        max_val = max(max(ch[0]) for ch in channels)
        if max_val == 0:
            return

        for data, color in channels:
            pen = QPen(color)
            pen.setWidthF(1.2)
            painter.setPen(pen)
            pts = []
            for i in range(256):
                x = pad + (i / 255) * (W - 2 * pad)
                y = H - pad - (data[i] / max_val) * (H - 2 * pad) * 0.92
                pts.append((x, y))
            for i in range(1, len(pts)):
                painter.drawLine(int(pts[i-1][0]), int(pts[i-1][1]),
                                 int(pts[i][0]), int(pts[i][1]))

        painter.end()
