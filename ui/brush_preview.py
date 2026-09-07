from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt5.QtCore import Qt, QRect, QPoint

class BrushPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.size = 10
        self.color = QColor(255,0,0)
        self.opacity = 100
        self.btype = "round"
        self.setFixedSize(120, 120)
        
        self.setStyleSheet("background-color: #13132a; border: 1px solid #00d4aa; border-radius: 6px;")
        
    def update_brush(self, size, color, opacity, btype):
        self.size = size
        self.color = color
        self.opacity = opacity
        self.btype = btype
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#13132a"))
        radius = max(8, int(self.size / 100 * 50))
        pen_color = QColor(self.color.red(), self.color.green(), self.color.blue(), int(self.opacity * 2.55))
        if self.btype == "square":
            painter.fillRect(QRect(60 - radius, 60 - radius, radius*2, radius*2), pen_color)
        else:
            painter.setBrush(QBrush(pen_color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRect(60 - radius, 60 - radius, radius * 2, radius * 2))
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor("#00d4aa"), 1))
        painter.drawRect(0, 0, 119, 119)
        painter.end()
            