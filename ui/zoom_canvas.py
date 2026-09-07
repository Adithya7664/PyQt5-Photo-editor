from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRect, QPoint, QPointF, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QPixmap, QCursor, QImage, QFont

class ZoomCanvas(QWidget):
    zoom_changed = pyqtSignal(float)
    crop_selected = pyqtSignal(QRect)
    color_picked = pyqtSignal(QColor)
    text_clicked = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #242424;")
        self.setMinimumHeight(400)
        self.mode = "none"

        self.base_pixmap  = None
        self.paint_pixmap = None

        self.zoom   = 1.0
        self.offset = QPointF(0, 0)

        self.pan_active   = False
        self.pan_start    = None

        self.drawing    = False
        self.last_point = None

        self.brush_size    = 10
        self.brush_color   = QColor(255, 0, 0)
        self.brush_opacity = 100
        self.brush_type    = "round"
        
        self.symmetry_h = False
        self.symmetry_v = False

        self.crop_start = None
        self.crop_rect  = None
        
        self.paint_history = []

        self.setMouseTracking(True)
        
    def set_mode(self, mode):
        self.mode = mode
        self.crop_rect = None
        self.update()
        cursors = {
            "crop" : Qt.CrossCursor,
            "paint" : Qt.CrossCursor,
            "erase" : Qt.CrossCursor,
            "eyedrop" : Qt.CrossCursor, 
            "none" : Qt.OpenHandCursor, 
            "text" : Qt.IBeamCursor
        }
        self.setCursor(cursors.get(mode, Qt.ArrowCursor))
        
    def update_brush(self, size, color, opacity, btype):
        self.brush_size    = size
        self.brush_color   = color
        self.brush_opacity = opacity
        self.brush_type    = btype
        
    def set_base_pixmap(self, pixmap):
        self.base_pixmap  = pixmap.copy()
        self.paint_pixmap = QPixmap(pixmap.size())
        self.paint_pixmap.fill(Qt.transparent)
        self.paint_history = []
        self.save_paint_state()
        self.zoom   = 1.0
        self.offset = QPointF(0, 0)
        self.update()

    def get_paint_merged(self):
        if self.base_pixmap is None:
            return None
        merged = self.base_pixmap.copy()
        painter = QPainter(merged)
        painter.drawPixmap(0, 0, self.paint_pixmap)
        painter.end()
        return merged
    
    # coordinate helpers
    def image_origin(self):
        if self.base_pixmap is None:
            return QPointF(0, 0)
        iw = self.base_pixmap.width()  * self.zoom
        ih = self.base_pixmap.height() * self.zoom
        ox = (self.width()  - iw) / 2 + self.offset.x()
        oy = (self.height() - ih) / 2 + self.offset.y()
        return QPointF(ox, oy)
    
    def widget_to_image(self, pos):
        if self.base_pixmap is None:
            return None
        origin = self.image_origin()
        x = (pos.x() - origin.x()) / self.zoom
        y = (pos.y() - origin.y()) / self.zoom
        iw = self.base_pixmap.width()
        ih = self.base_pixmap.height()
        if 0 <= x <= iw and 0 <= y <= ih:
            return QPointF(x, y)
        return None

    def image_to_widget(self, pt):
        origin = self.image_origin()
        return QPointF(
            pt.x() * self.zoom + origin.x(),
            pt.y() * self.zoom + origin.y()
        )
    # Mouse events
    def wheelEvent(self, event):
        if self.base_pixmap is None:
            return
        delta     = event.angleDelta().y()
        factor    = 1.15 if delta > 0 else 1 / 1.15
        new_zoom  = max(0.1, min(self.zoom * factor, 20.0))

        mouse_pos = QPointF(event.pos())
        origin    = self.image_origin()
        img_x     = (mouse_pos.x() - origin.x()) / self.zoom
        img_y     = (mouse_pos.y() - origin.y()) / self.zoom

        self.zoom = new_zoom

        new_origin_x = mouse_pos.x() - img_x * self.zoom
        new_origin_y = mouse_pos.y() - img_y * self.zoom
        iw = self.base_pixmap.width()  * self.zoom
        ih = self.base_pixmap.height() * self.zoom
        cx = (self.width()  - iw) / 2
        cy = (self.height() - ih) / 2
        self.offset = QPointF(new_origin_x - cx, new_origin_y - cy)
        self.update()
        self.zoom_changed.emit(self.zoom)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton or (
            event.button() == Qt.LeftButton and self.mode == "none"
        ):
            self.pan_active = True
            self.pan_start  = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            return

        if event.button() != Qt.LeftButton:
            return

        if self.mode == "crop":
            self.crop_start = event.pos()
            self.crop_rect  = QRect(self.crop_start, self.crop_start)

        elif self.mode == "eyedrop":
            self.pick_color(event.pos())
            
        elif self.mode == "text":
            pt = self.widget_to_image(event.pos())
            if pt:
                self.text_clicked.emit(pt)

        elif self.mode in ("paint", "erase"):
            pt = self.widget_to_image(event.pos())
            if pt:
                self.drawing    = True
                self.last_point = pt
                self.draw_point(pt)
                
    def mouseMoveEvent(self, event):
        if self.pan_active:
            delta       = event.pos() - self.pan_start
            self.offset += QPointF(delta)
            self.pan_start = event.pos()
            self.update()
            return

        if self.mode == "crop" and self.crop_start:
            self.crop_rect = QRect(self.crop_start, event.pos()).normalized()
            self.update()

        elif self.mode in ("paint", "erase") and self.drawing:
            pt = self.widget_to_image(event.pos())
            if pt and self.last_point:
                self.draw_line(self.last_point, pt)
                self.last_point = pt
                
    def mouseReleaseEvent(self, event):
        if event.button() in (Qt.MiddleButton, Qt.LeftButton) and self.pan_active:
            self.pan_active = False
            self.setCursor(Qt.ArrowCursor)
            return

        if self.mode == "crop" and self.crop_rect:
            self.crop_selected.emit(self.crop_rect)

        elif self.mode in ("paint", "erase"):
            self.drawing    = False
            self.last_point = None
            self.save_paint_state()
            
    # painting
    def draw_point(self, pt):
        painter = QPainter(self.paint_pixmap)
        self.configure_painter(painter)
        painter.drawPoint(pt.toPoint())
        if self.symmetry_h:
            w = self.base_pixmap.width()
            painter.drawPoint(QPointF(w - pt.x(), pt.y()).toPoint())
        if self.symmetry_v:
            h = self.base_pixmap.height()
            painter.drawPoint(QPointF(pt.x(), h - pt.y()).toPoint())
        painter.end()
        self.update()

    def draw_line(self, p1, p2):
        painter = QPainter(self.paint_pixmap)
        self.configure_painter(painter)
        painter.drawLine(p1.toPoint(), p2.toPoint())
        if self.symmetry_h:
            w = self.base_pixmap.width()
            painter.drawLine(QPointF(w - p1.x(), p1.y()).toPoint(),
                            QPointF(w - p2.x(), p2.y()).toPoint())
        if self.symmetry_v:
            h = self.base_pixmap.height()
            painter.drawLine(QPointF(p1.x(), h - p1.y()).toPoint(),
                            QPointF(p2.x(), h - p2.y()).toPoint())
        painter.end()
        self.update()

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
            cap  = Qt.RoundCap   if self.brush_type in ("round", "soft") else Qt.SquareCap
            join = Qt.RoundJoin  if self.brush_type in ("round", "soft") else Qt.MiterJoin
            pen  = QPen(pen_color, self.brush_size, Qt.SolidLine, cap, join)
        painter.setPen(pen)

    def pick_color(self, pos):
        if self.base_pixmap is None:
            return
        merged = self.get_paint_merged()
        img    = merged.toImage()
        pt     = self.widget_to_image(pos)
        if pt:
            color = QColor(img.pixel(pt.toPoint()))
            self.color_picked.emit(color)
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#1a1a1a"))

        # Draw grid
        grid_size = 30
        painter.setPen(QPen(QColor("#2a2a2a"), 1))
        for x in range(0, self.width(), grid_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), grid_size):
            painter.drawLine(0, y, self.width(), y)

        if self.base_pixmap is None:
            painter.setPen(QColor("#00d4aa"))
            painter.setFont(QFont("Segoe UI", 14))
            painter.drawText(self.rect(), Qt.AlignCenter, "Open an image to get started")
            painter.end()
            return

        origin = self.image_origin()
        iw = int(self.base_pixmap.width()  * self.zoom)
        ih = int(self.base_pixmap.height() * self.zoom)
        target = QRect(int(origin.x()), int(origin.y()), iw, ih)

        painter.drawPixmap(target, self.base_pixmap)
        painter.drawPixmap(target, self.paint_pixmap)

        if self.mode == "crop" and self.crop_rect:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 80))
            painter.fillRect(self.crop_rect, QColor(0, 212, 170, 30))
            pen = QPen(QColor("#00d4aa"), 2, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(self.crop_rect)

        painter.end()
        
    def save_paint_state(self):
        if self.paint_pixmap is not None:
            self.paint_history.append(self.paint_pixmap.copy())
            if len(self.paint_history) > 20:
                self.paint_history.pop(0)
                
    def undo_paint(self):
        if len(self.paint_history) > 1:
            self.paint_history.pop()
            self.paint_pixmap = self.paint_history[-1].copy()
            self.update()
        elif len(self.paint_history) == 1:
            self.paint_history.pop()
            self.paint_pixmap.fill(Qt.transparent)
            self.update()
            
    def set_symmetry_h(self, val):
        self.symmetry_h = val
        
    def set_symmetry_v(self, val):
        self.symmetry_v = val
        
    def draw_text(self, pt, text, font_size, color, opacity):
        painter = QPainter(self.paint_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen_color = QColor(color.red(), color.green(), color.blue(), int(opacity * 2.55))
        painter.setPen(QPen(pen_color))
        painter.setFont(QFont("Arial", font_size))
        painter.drawText(pt.toPoint(), text)
        painter.end()
        self.save_paint_state()
        self.update()