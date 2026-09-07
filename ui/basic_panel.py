from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QLabel, QSlider, QPushButton, QTabWidget
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QImage, QPixmap
from ui.histogram import Histogram

class BasicPanel(QWidget):
    def __init__(self, editor, refresh_callback, canvas):
        super().__init__()
        self.editor = editor
        self.refresh = refresh_callback
        self.canvas = canvas
        self.sliders = {}
        self.preview_base = None
        self.build_ui()

    def build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(8)

        self.inner_tabs = QTabWidget()
        self.inner_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #1c1c2e;
            }
            QTabBar::tab {
                background-color: #13132a;
                color: #666666;
                padding: 4px 16px;
                font-size: 9pt;
                font-weight: bold;
                border: none;
            }
            QTabBar::tab:selected {
                color: #00d4aa;
                border-bottom: 2px solid #00d4aa;
                background-color: #1c1c2e;
            }
            QTabBar::tab:hover { color: #0099cc; background-color: #202038; }
        """)

        self.inner_tabs.addTab(self.make_tone_tab(),   "Tone")
        self.inner_tabs.addTab(self.make_color_tab(),  "Color")
        self.inner_tabs.addTab(self.make_detail_tab(), "Detail")
        
        self.histogram = Histogram()
        
        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)
        top_layout.addWidget(self.inner_tabs, stretch=1)
        top_layout.addWidget(self.histogram, stretch=1)

        main_layout.addLayout(top_layout, stretch=1)
        main_layout.addLayout(self.make_buttons())

    def slider_style(self):
        return """
            QSlider::groove:horizontal {
                height: 5px;
                background: #2a2a2a;
                border-radius: 2px;
                border: 1px solid #333333;
            }
            QSlider::handle:horizontal {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                    fx:0.5, fy:0.5, stop:0 #ffffff, stop:1 #00d4aa);
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
                border: 1px solid #00d4aa;
            }
            QSlider::handle:horizontal:hover {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                    fx:0.5, fy:0.5, stop:0 #ffffff, stop:1 #00ffcc);
                width: 18px;
                height: 18px;
                margin: -7px 0;
                border-radius: 9px;
                border: 2px solid #00ffcc;
            }
            QSlider::handle:horizontal:pressed {
                background: #ffffff;
                border: 2px solid #ffffff;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0099cc, stop:1 #00d4aa);
                border-radius: 2px;
            }
        """

    def make_slider_row(self, label, key, mn, mx, default):
        row = QHBoxLayout()
        row.setSpacing(2)

        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lbl.setStyleSheet("color: #cccccc;")
        lbl.setFixedWidth(70)

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(mn)
        slider.setMaximum(mx)
        slider.setValue(default)
        slider.setFixedHeight(24)
        slider.setFixedWidth(200)
        slider.setStyleSheet(self.slider_style())

        val_lbl = QLabel(str(default))
        val_lbl.setFont(QFont("Segoe UI", 10))
        val_lbl.setFont(QFont("Segoe UI", 10))
        val_lbl.setStyleSheet("""
            color: #00d4aa;
            background-color: #252525;
            border: 1px solid #333333;
            border-radius: 3px;
            padding: 1px 4px;
        """)
        val_lbl.setFixedWidth(36)
        val_lbl.setAlignment(Qt.AlignCenter)

        slider.valueChanged.connect(lambda v, l=val_lbl: l.setText(str(v)))
        slider.sliderMoved.connect(lambda v: self.apply_all())
        slider.sliderReleased.connect(self._do_apply)

        self.sliders[key] = slider
        row.addWidget(lbl)
        row.addWidget(slider)
        row.addWidget(val_lbl)
        return row

    def make_tab_widget(self, rows):
        w = QWidget()
        w.setStyleSheet("background-color: #1c1c2e;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(4)
        for row in rows:
            layout.addLayout(row)
        return w
    
    def make_tone_tab(self):
        return self.make_tab_widget([
            self.make_slider_row("Brightness", "Brightness", 0,    200,  100),
            self.make_slider_row("Contrast",   "Contrast",   0,    200,  100),
            self.make_slider_row("Exposure",   "Exposure",  -100,  100,    0),
            self.make_slider_row("Highlights", "Highlights",-100,  100,    0),
            self.make_slider_row("Shadows",    "Shadows",   -100,  100,    0),
        ])

    def make_color_tab(self):
        return self.make_tab_widget([
            self.make_slider_row("Saturation", "Saturation",   0,  200,  100),
            self.make_slider_row("Vibrance",   "Vibrance",  -100,  100,    0),
            self.make_slider_row("Temperature","Temperature",-100, 100,    0),
            self.make_slider_row("Hue",        "Hue",        -180, 180,    0),
        ])

    def make_detail_tab(self):
        return self.make_tab_widget([
            self.make_slider_row("Sharpness", "Sharpness", 0, 200, 100),
            self.make_slider_row("Blur",      "Blur",      0,  20,   0),
            self.make_slider_row("Vignette",  "Vignette",  0, 100,   0),
        ])

    def make_buttons(self):
        layout = QHBoxLayout()
        layout.setSpacing(8)

        buttons = [
            ("Rotate 90°", self.on_rotate),
            ("Flip H",     self.on_flip_h),
            ("Flip V",     self.on_flip_v),
            ("Remove BG",  self.on_remove_bg),
            ("Crop",       self.on_crop),
            ("Auto Enhance",self.on_auto_enhance),
        ]

        style = """
            QPushButton {
                background-color: #1e1e1e;
                color: #00d4aa;
                border: 1px solid #00d4aa;
                border-radius: 5px;
                padding: 7px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00d4aa;
                color: #1a1a1a;
                border: 1px solid #00ffcc;
            }
            QPushButton:pressed {
                background-color: #009988;
                color: #ffffff;
            }
        """

        for label, callback in buttons:
            btn = QPushButton(label)
            btn.setStyleSheet(style)
            btn.setFixedHeight(32)
            btn.clicked.connect(callback)
            layout.addWidget(btn)

        return layout

    def get_val(self, key, default=100):
        return self.sliders[key].value() if key in self.sliders else default

    def apply_all(self):
        if self.editor.current is None or self.preview_base is None:
            return
        from PIL import ImageEnhance
        b  = self.get_val("Brightness") / 100
        c  = self.get_val("Contrast")   / 100
        s  = self.get_val("Saturation") / 100
        sh = self.get_val("Sharpness")  / 100
        img = ImageEnhance.Brightness(self.preview_base).enhance(b)
        img = ImageEnhance.Contrast(img).enhance(c)
        img = ImageEnhance.Color(img).enhance(s)
        img = ImageEnhance.Sharpness(img).enhance(sh)
        self.refresh_preview(img)
        self.histogram.update_image(img)

    def _do_apply(self):
        if self.editor.current is None:
            return
        self.editor.save_state()
        self.editor.apply_adjustments(
            brightness  = self.get_val("Brightness") / 100,
            contrast    = self.get_val("Contrast")   / 100,
            saturation  = self.get_val("Saturation") / 100,
            sharpness   = self.get_val("Sharpness")  / 100,
            temperature = self.get_val("Temperature", 0),
            exposure    = self.get_val("Exposure", 0) / 100,
            highlights  = self.get_val("Highlights", 0) / 100,
            shadows     = self.get_val("Shadows", 0) / 100,
            vibrance    = self.get_val("Vibrance", 0) / 100,
            hue         = self.get_val("Hue", 0),
            blur        = self.get_val("Blur", 0),
            vignette    = self.get_val("Vignette", 0) / 100,
        )
        self.refresh()
        self.histogram.update_image(self.editor.current)

    def refresh_preview(self, pil_image):
        image = pil_image.convert("RGBA")
        data  = image.tobytes("raw", "RGBA")
        qt_image = QImage(data, image.width, image.height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qt_image)
        scaled = pixmap.scaled(self.canvas.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.canvas.set_base_pixmap(scaled)

    def update_preview_base(self, pil_image):
        from PIL import Image
        preview = pil_image.copy()
        preview.thumbnail((600, 600), Image.LANCZOS)
        self.preview_base = preview

    def on_rotate(self):
        if self.editor.current:
            self.editor.rotate(90)
            self.refresh()

    def on_flip_h(self):
        if self.editor.current:
            self.editor.flip_horizontal()
            self.refresh()

    def on_flip_v(self):
        if self.editor.current:
            self.editor.flip_vertical()
            self.refresh()

    def on_remove_bg(self):
        if self.editor.current:
            self.editor.remove_background()
            self.refresh()

    def on_crop(self):
        self.canvas.set_mode("crop")
        
    def reset_sliders(self):
        defaults = {
            "Brightness": 100, "Contrast": 100,
            "Saturation": 100, "Sharpness": 100,
            "Exposure": 0, "Highlights": 0, "Shadows": 0,
            "Vibrance": 0, "Temperature": 0,
            "Hue": 0, "Blur": 0, "Vignette": 0,
        }
        for key, val in defaults.items():
            if key in self.sliders:
                self.sliders[key].blockSignals(True)
                self.sliders[key].setValue(val)
                self.sliders[key].blockSignals(False)
                
    def on_auto_enhance(self):
        if self.editor.current is None:
            return
        from PIL import ImageOps, ImageEnhance
        self.editor.save_state()
        img = self.editor.current.convert("RGB")
        img = ImageOps.autocontrast(img, cutoff=1)
        img = ImageEnhance.Color(img).enhance(1.15)
        img = ImageEnhance.Brightness(img).enhance(1.05)
        self.editor.current = img.convert("RGBA")
        self.editor.base = self.editor.current.copy()
        self.reset_sliders()
        self.update_preview_base(self.editor.current)
        self.refresh()
        self.histogram.update_image(self.editor.current)