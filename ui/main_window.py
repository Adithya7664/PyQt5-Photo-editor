import os
import sys
import io
from PyQt5.QtWidgets import (
    QMainWindow, QLabel, QFileDialog, QAction,
    QMenuBar, QMenu, QStatusBar, QWidget,
    QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image
from editor import editor
from ui.basic_panel import BasicPanel
from ui.paint_panel import PaintPanel
from ui.zoom_canvas import ZoomCanvas
from ui.style_panel import StylePanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.editor = editor()
        self.setWindowTitle("GenPhoto")
        self.setMinimumSize(1100, 700)
        self.apply_theme()
        self.recent_files = []
        self._load_recent_files()
        self.build_menu()
        self.build_layout()
        self.statusBar().showMessage("Open an image to get started")

    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1a1a1a;
                color: #e0e0e0;
            }
            QMenuBar {
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
            QStatusBar {
                background-color: #141414;
                color: #aaaaaa;
                font-size: 10pt;
                border-top: 1px solid #00d4aa;
                padding: 2px 8px;
            }
            QTabWidget::pane {
                border: none;
                background-color: #1c1c2e;
            }
            QTabBar::tab {
                background-color: #16162a;
                color: #888888;
                padding: 10px 28px;
                font-size: 11pt;
                font-weight: bold;
                border: none;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                color: #00d4aa;
                border-bottom: 3px solid #00d4aa;
                background-color: #1c1c2e;
            }
            QTabBar::tab:hover {
                color: #0099cc;
                background-color: #222238;
            }
            QMenu {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
            }
            QMenu::item:selected {
                background-color: #00d4aa;
                color: #1a1a1a;
            }
        """)

    def build_menu(self):
        self.menuBar().hide()

        self.top_bar = QWidget()
        self.top_bar.setFixedHeight(36)
        self.top_bar.setStyleSheet("background-color: #311c1c;")

        layout = QHBoxLayout(self.top_bar)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(6)

        menu_style = """
            QPushButton {
                background-color: transparent;
                color: #e0e0e0;
                border: none;
                padding: 4px 10px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-radius: 4px;
            }
            QPushButton::menu-indicator { width: 0; }
        """

        btn_style = """
            QPushButton {
                background-color: transparent;
                color: #00d4aa;
                border: 1px solid #00d4aa;
                border-radius: 4px;
                padding: 3px 14px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #00d4aa;
                color: #1a1a1a;
            }
        """

        # File menu
        file_btn = QPushButton("File")
        file_btn.setStyleSheet(menu_style)
        file_menu = QMenu(self)
        file_menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
            }
            QMenu::item:selected {
                background-color: #00d4aa;
                color: #1a1a1a;
            }
        """)
        open_action = file_menu.addAction("Open Image")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_image)
        save_action = file_menu.addAction("Save")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_image)
        self.recent_menu = file_menu.addMenu("Recent Files")
        self._load_recent_files()
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_btn.setMenu(file_menu)

        # Undo / Reset
        undo_btn = QPushButton("↩  Undo")
        undo_btn.setStyleSheet(btn_style)
        undo_btn.clicked.connect(self.undo)

        reset_btn = QPushButton("↺  Reset")
        reset_btn.setStyleSheet(btn_style)
        reset_btn.clicked.connect(self.reset)
        
        self.ba_btn = QPushButton("⊕  Before/After")
        self.ba_btn.setStyleSheet(btn_style)
        self.ba_btn.setEnabled(False)
        self.ba_btn.pressed.connect(self._show_original)
        self.ba_btn.released.connect(self._show_current)

        # Branding
        brand = QLabel("  ✦ GenPhoto  ")
        brand.setStyleSheet("color: #00d4aa; font-size: 11pt; font-weight: bold;")

        # Shortcuts (no menu needed)
        undo_sc = QAction(self)
        undo_sc.setShortcut("Ctrl+Z")
        undo_sc.triggered.connect(self.undo)
        self.addAction(undo_sc)

        reset_sc = QAction(self)
        reset_sc.setShortcut("Ctrl+R")
        reset_sc.triggered.connect(self.reset)
        self.addAction(reset_sc)

        layout.addWidget(file_btn)
        layout.addStretch()
        layout.addWidget(undo_btn)
        layout.addWidget(reset_btn)
        layout.addWidget(self.ba_btn)
        layout.addStretch()
        layout.addWidget(brand)

    def build_layout(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.top_bar)

        self.canvas = ZoomCanvas()
        self.canvas.crop_selected.connect(self.apply_crop)
        self.canvas.setStyleSheet("""
            background-color: #242424;
            border: 1px solid #00d4aa;
            border-radius: 4px;
        """)
        canvas_wrapper = QWidget()
        canvas_wrapper.setStyleSheet("background-color: #1a1a1a; padding: 8px;")
        wrapper_layout = QVBoxLayout(canvas_wrapper)
        wrapper_layout.setContentsMargins(8, 8, 8, 8)
        wrapper_layout.addWidget(self.canvas)
        main_layout.addWidget(canvas_wrapper, stretch=1)
        
        seperator = QFrame()
        seperator.setFixedHeight(2)
        seperator.setStyleSheet("background-color: #00d4aa;")
        main_layout.addWidget(seperator)
        
        self.canvas.zoom_changed.connect(lambda z: self.statusBar().showMessage(f"Zoom: {int(z*100)}%"))

        self.tabs = QTabWidget()
        self.tabs.setFixedHeight(250)
        self.basic_panel = BasicPanel(self.editor, self.refresh_canvas, self.canvas)
        self.tabs.addTab(self.basic_panel, "Basic")
        self.paint_panel = PaintPanel(self.canvas)
        self.tabs.addTab(self.paint_panel, "Paint")
        self.style_panel = StylePanel(self.editor, self.refresh_canvas)
        self.tabs.addTab(self.style_panel, "Styles")
        main_layout.addWidget(self.tabs)

    def open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if file_path:
            self.editor.load(file_path)
            self.ba_btn.setEnabled(True)
            self._add_recent_file(file_path)
            self.basic_panel.update_preview_base(self.editor.base)
            self.refresh_canvas()
            self.basic_panel.histogram.update_image(self.editor.current)
            self.statusBar().showMessage(f"Opened: {file_path}")

    def save_image(self):
        if self.editor.current is None:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "", "PNG (*.png);;JPEG (*.jpg)"
        )
        if file_path:
            self.editor.save(file_path)
            self.statusBar().showMessage(f"Saved: {file_path}")

    def refresh_canvas(self):
        if self.editor.current is None:
            return
        image = self.editor.current.convert("RGBA")
        data = image.tobytes("raw", "RGBA")
        qt_image = QImage(data, image.width, image.height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qt_image)
        scaled = pixmap.scaled(self.canvas.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.canvas.set_base_pixmap(scaled)
        self.update_status()
        self.basic_panel.histogram.update_image(self.editor.current)

    def undo(self):
        if self.tabs.currentIndex() == 1:
            self.canvas.undo_paint()
        else: 
            self.editor.undo()
            self.refresh_canvas()

    def reset(self):
        if self.editor.original is None:
            return
        self.basic_panel.reset_sliders()
        self.editor.reset()
        self.basic_panel.update_preview_base(self.editor.base)
        self.refresh_canvas()
        
    def apply_crop(self, rect):
        if self.editor.current is None:
            return
        from PyQt5.QtCore import QPointF
        tl = self.canvas.widget_to_image(QPointF(rect.topLeft()))
        br = self.canvas.widget_to_image(QPointF(rect.bottomRight()))
        if tl is None or br is None:
            return
        img_w, img_h = self.editor.current.size
        bw = self.canvas.base_pixmap.width()
        bh = self.canvas.base_pixmap.height()
        x1 = int(tl.x() * img_w / bw)
        y1 = int(tl.y() * img_h / bh)
        x2 = int(br.x() * img_w / bw)
        y2 = int(br.y() * img_h / bh)
        x1 = max(0, min(x1, img_w))
        y1 = max(0, min(y1, img_h))
        x2 = max(0, min(x2, img_w))
        y2 = max(0, min(y2, img_h))
        if x2 > x1 and y2 > y1:
            self.editor.crop(x1, y1, x2, y2)
            self.canvas.set_mode("none")
            self.refresh_canvas()
          
    def update_status(self):
        zoom_pct = int(self.canvas.zoom * 100)
        self.statusBar().showMessage(f"Zoom: {zoom_pct}%")
        
    def _load_recent_files(self):
        import json
        path = os.path.join(os.path.dirname(__file__), "recent_files.json")
        try:
            with open(path) as f:
                self.recent_files = json.load(f)
        except:
            self.recent_files = []

    def _save_recent_files(self):
        import json
        path = os.path.join(os.path.dirname(__file__), "recent_files.json")
        with open(path, "w") as f:
            json.dump(self.recent_files, f)

    def _add_recent_file(self, file_path):
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:5]
        self._save_recent_files()
        self._rebuild_recent_menu()

    def _rebuild_recent_menu(self):
        self.recent_menu.clear()
        if not self.recent_files:
            self.recent_menu.addAction("No recent files").setEnabled(False)
        for path in self.recent_files:
            action = self.recent_menu.addAction(os.path.basename(path))
            action.setToolTip(path)
            action.triggered.connect(lambda checked, p=path: self._open_recent(p))

    def _open_recent(self, file_path):
        if not os.path.exists(file_path):
            self.statusBar().showMessage(f"File not found: {file_path}")
            return
        self.editor.load(file_path)
        self.basic_panel.update_preview_base(self.editor.base)
        self.refresh_canvas()
        self.basic_panel.histogram.update_image(self.editor.current)
        self._add_recent_file(file_path)
        self.statusBar().showMessage(f"Opened: {file_path}")
        
    def _show_original(self):
        if self.editor.original is None:
            return
        image = self.editor.original.convert("RGBA")
        data = image.tobytes("raw", "RGBA")
        qt_image = QImage(data, image.width, image.height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qt_image)
        scaled = pixmap.scaled(self.canvas.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.canvas.set_base_pixmap(scaled)

    def _show_current(self):
        self.refresh_canvas()

          
    