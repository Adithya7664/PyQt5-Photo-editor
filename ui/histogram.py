import numpy as np
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QRect

class Histogram(QWidget):
    def __init__(self):
        super().__init__()
        self.r_hist = None
        self.g_hist = None
        self.b_hist = None
        self.setMinimumWidth(180)
        self.setStyleSheet("background-color: #13132a; border: 1px solid #00d4aa; border-radius: 4px;")
        
    def update_image(self, pil_image):
        if pil_image is None:
            self.r_hist = None
            self.update()
            return
        arr = np.array(pil_image.convert("RGB"))
        self.r_hist = np.bincount(arr[:,:,0].flatten(), minlength=256).astype(np.float32)
        self.g_hist = np.bincount(arr[:,:,1].flatten(), minlength=256).astype(np.float32)
        self.b_hist = np.bincount(arr[:,:,2].flatten(), minlength=256).astype(np.float32)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#13132a"))

        if self.r_hist is None:
            painter.setPen(QColor("#444444"))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(self.rect(), Qt.AlignCenter, "Open an image")
            painter.end()
            return

        w, h = self.width() - 2, self.height() - 2
        pad = 1
        max_val = max(self.r_hist.max(), self.g_hist.max(), self.b_hist.max())
        if max_val == 0:
            painter.end()
            return

        bar_w = w / 256

        for i in range(256):
            x = pad + int(i * bar_w)
            bw = max(1, int(bar_w))

            rh = int((self.r_hist[i] / max_val) * h)
            if rh > 0:
                painter.fillRect(QRect(x, pad + h - rh, bw, rh), QColor(255, 80, 80, 130))

            gh = int((self.g_hist[i] / max_val) * h)
            if gh > 0:
                painter.fillRect(QRect(x, pad + h - gh, bw, gh), QColor(80, 220, 160, 130))

            bh = int((self.b_hist[i] / max_val) * h)
            if bh > 0:
                painter.fillRect(QRect(x, pad + h - bh, bw, bh), QColor(80, 180, 255, 130))

        painter.setPen(QPen(QColor("#00d4aa"), 1))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
        painter.end()