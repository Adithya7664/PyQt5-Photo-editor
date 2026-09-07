from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QPixmap

class Canvas(QLabel):
    crop_selected = pyqtSignal(QRect)

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #242424;")
        self.setMinimumHeight(400)
        self.mode = "none"

        self.crop_start = None
        self.crop_rect = None

        self.brush_size = 10
        self.brush_color = QColor(255, 0, 0)
        self.brush_opacity = 100
        self.brush_type = "round"
        self.last_point = None
        self.drawing = False

        self.base_pixmap = None
        self.paint_pixmap = None

    def set_mode(self, mode):
        self.mode = mode
        self.crop_rect = None
        self.update()
        if mode in ("crop", "paint", "erase"):
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def update_brush(self, size, color, opacity, btype):
        self.brush_size = size
        self.brush_color = color
        self.brush_opacity = opacity
        self.brush_type = btype

    def set_base_pixmap(self, pixmap):
        self.base_pixmap = pixmap.copy()
        self.paint_pixmap = QPixmap(pixmap.size())
        self.paint_pixmap.fill(Qt.transparent)
        self.render_composite()

    def render_composite(self):
        if self.base_pixmap is None:
            return
        composite = self.base_pixmap.copy()
        painter = QPainter(composite)
        painter.drawPixmap(0, 0, self.paint_pixmap)
        painter.end()
        super().setPixmap(composite)

    def get_image_offset(self):
        pixmap = self.pixmap()
        if pixmap is None:
            return 0, 0
        return (self.width() - pixmap.width()) // 2, (self.height() - pixmap.height()) // 2

    def canvas_to_image(self, pos):
        pixmap = self.pixmap()
        if pixmap is None:
            return None
        ox, oy = self.get_image_offset()
        x = pos.x() - ox
        y = pos.y() - oy
        if 0 <= x <= pixmap.width() and 0 <= y <= pixmap.height():
            return QPoint(x, y)
        return None

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        if self.mode == "crop":
            self.crop_start = event.pos()
            self.crop_rect = QRect(self.crop_start, self.crop_start)
        elif self.mode in ("paint", "erase"):
            self.drawing = True
            pt = self.canvas_to_image(event.pos())
            if pt:
                self.last_point = pt
                self.draw_point(pt)

    def mouseMoveEvent(self, event):
        if self.mode == "crop" and self.crop_start:
            self.crop_rect = QRect(self.crop_start, event.pos()).normalized()
            self.update()
        elif self.mode in ("paint", "erase") and self.drawing:
            pt = self.canvas_to_image(event.pos())
            if pt and self.last_point:
                self.draw_line(self.last_point, pt)
                self.last_point = pt

    def mouseReleaseEvent(self, event):
        if self.mode == "crop" and self.crop_rect:
            self.crop_selected.emit(self.crop_rect)
        elif self.mode in ("paint", "erase"):
            self.drawing = False
            self.last_point = None

    def draw_point(self, pt):
        painter = QPainter(self.paint_pixmap)
        self.configure_painter(painter)
        painter.drawPoint(pt)
        painter.end()
        self.render_composite()

    def draw_line(self, p1, p2):
        painter = QPainter(self.paint_pixmap)
        self.configure_painter(painter)
        painter.drawLine(p1, p2)
        painter.end()
        self.render_composite()

    def configure_painter(self, painter):
        painter.setRenderHint(QPainter.Antialiasing)
        if self.mode == "erase":
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            pen = QPen(Qt.transparent, self.brush_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        else:
            pen_color = QColor(
                self.brush_color.red(),
                self.brush_color.green(),
                self.brush_color.blue(),
                int(self.brush_opacity * 2.55)
            )
            cap  = Qt.RoundCap  if self.brush_type in ("round", "soft") else Qt.SquareCap
            join = Qt.RoundJoin if self.brush_type in ("round", "soft") else Qt.MiterJoin
            pen = QPen(pen_color, self.brush_size, Qt.SolidLine, cap, join)
        painter.setPen(pen)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.mode == "crop" and self.crop_rect:
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor(0, 0, 0, 80))
            painter.fillRect(self.crop_rect, QColor(0, 212, 170, 30))
            pen = QPen(QColor("#00d4aa"), 2, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(self.crop_rect)
            painter.end()

    def get_paint_merged(self):
        if self.base_pixmap is None:
            return None
        merged = self.base_pixmap.copy()
        painter = QPainter(merged)
        painter.drawPixmap(0, 0, self.paint_pixmap)
        painter.end()
        return merged