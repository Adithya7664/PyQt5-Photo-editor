from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QLabel, QSlider, QPushButton, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

INSTANT_STYLES = [
    ("Pencil Sketch", "sketch"),
    ("Cartoon",       "cartoon"),
    ("Watercolor",    "watercolor"),
    ("Oil Painting",  "oil"),
    ("Sepia",         "sepia"),
    ("Fade",          "fade"),
    ("Vivid",         "vivid"),
    ("Cinematic",     "cinematic"),
    ("B&W",           "bw"),
]

NEURAL_STYLES = [
    ("Anime / Ghibli", "anime"),
    ("Starry Night",   "starry"),
    ("Mosaic",         "mosaic"),
    ("Candy",          "candy"),
    ("Rain Princess",  "rain"),
]

class StyleWorker(QThread):
    finished = pyqtSignal(object)
    error    = pyqtSignal(str)

    def __init__(self, image, style_key, intensity):
        super().__init__()
        self.image     = image
        self.style_key = style_key
        self.intensity = intensity

    def run(self):
        try:
            from styles.style_engine import (
                apply_sketch, apply_cartoon, apply_watercolor, apply_oil,
                apply_sepia, apply_fade, apply_vivid, apply_cinematic,
                apply_bw, apply_anime, apply_starry, apply_mosaic,
                apply_candy, apply_rain,
            )
            fns = {
                "sketch": apply_sketch, "cartoon": apply_cartoon,
                "watercolor": apply_watercolor, "oil": apply_oil,
                "sepia": apply_sepia, "fade": apply_fade,
                "vivid": apply_vivid, "cinematic": apply_cinematic,
                "bw": apply_bw, "anime": apply_anime,
                "starry": apply_starry, "mosaic": apply_mosaic,
                "candy": apply_candy, "rain": apply_rain,
            }
            result = fns[self.style_key](self.image, self.intensity)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class StylePanel(QWidget):
    def __init__(self, editor, refresh_callback):
        super().__init__()
        self.editor       = editor
        self.refresh      = refresh_callback
        self.worker       = None
        self.active_style = None
        self.active_btn   = None
        self.build_ui()

    def build_ui(self):
        self.setStyleSheet("background-color: #1c1c2e;")
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 8, 16, 8)
        main_layout.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(6)
        left.addLayout(self._make_section("Instant Styles", INSTANT_STYLES))
        left.addSpacing(8)
        left.addLayout(self._make_section("Neural Styles", NEURAL_STYLES))
        left.addStretch()
        main_layout.addLayout(left, stretch=3)

        right = QVBoxLayout()
        right.setSpacing(8)

        int_lbl = QLabel("Intensity")
        int_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        int_lbl.setStyleSheet("color: #888888;")
        right.addWidget(int_lbl)

        slider_row = QHBoxLayout()
        self.intensity_slider = QSlider(Qt.Horizontal)
        self.intensity_slider.setMinimum(0)
        self.intensity_slider.setMaximum(100)
        self.intensity_slider.setValue(100)
        self.intensity_slider.setFixedHeight(20)
        self.intensity_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #252540; border-radius: 2px; }
            QSlider::handle:horizontal { background: #00d4aa; width: 12px; height: 12px; margin: -4px 0;
border-radius: 6px; }
            QSlider::sub-page:horizontal { background: #00d4aa; border-radius: 2px; }
        """)
        self.intensity_val = QLabel("100")
        self.intensity_val.setStyleSheet("color: #00d4aa; font-size: 9pt;")
        self.intensity_val.setFixedWidth(28)
        self.intensity_val.setAlignment(Qt.AlignCenter)
        self.intensity_slider.valueChanged.connect(lambda v: self.intensity_val.setText(str(v)))
        slider_row.addWidget(self.intensity_slider)
        slider_row.addWidget(self.intensity_val)
        right.addLayout(slider_row)

        self.apply_btn = QPushButton("✦  Apply Style")
        self.apply_btn.setFixedHeight(42)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d4aa; color: #1a1a1a;
                border: none; border-radius: 6px;
                font-size: 12pt; font-weight: bold;
            }
            QPushButton:hover    { background-color: #00ffcc; }
            QPushButton:disabled { background-color: #2a2a2a; color: #555555; }
        """)
        self.apply_btn.clicked.connect(self.apply_style)
        right.addWidget(self.apply_btn)

        self.status_lbl = QLabel("Select a style then click Apply")
        self.status_lbl.setStyleSheet("color: #888888; font-size: 9pt;")
        self.status_lbl.setWordWrap(True)
        right.addWidget(self.status_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar { background-color: #13132a; border: 1px solid #00d4aa; border-radius: 3px; }
            QProgressBar::chunk { background-color: #00d4aa; }
        """)
        right.addWidget(self.progress_bar)
        right.addStretch()
        main_layout.addLayout(right, stretch=1)

    def _make_section(self, title, styles):
        layout = QVBoxLayout()
        layout.setSpacing(4)
        lbl = QLabel(title)
        lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        lbl.setStyleSheet("color: #888888;")
        layout.addWidget(lbl)
        grid = QGridLayout()
        grid.setSpacing(4)
        btn_style = """
            QPushButton {
                background-color: #13132a; color: #00d4aa;
                border: 1px solid #00d4aa; border-radius: 4px;
                padding: 6px; font-size: 9pt;
            }
            QPushButton:hover   { background-color: #00d4aa; color: #1a1a1a; }
            QPushButton:checked { background-color: #00d4aa; color: #1a1a1a; }
        """
        for i, (label, key) in enumerate(styles):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda checked, k=key, b=btn: self._select_style(k, b))
            grid.addWidget(btn, i // 3, i % 3)
        layout.addLayout(grid)
        return layout

    def _select_style(self, key, btn):
        if self.active_btn and self.active_btn is not btn:
            self.active_btn.setChecked(False)
        self.active_style = key
        self.active_btn   = btn
        btn.setChecked(True)
        self.status_lbl.setText("Ready — click Apply")

    def apply_style(self):
        if self.editor.current is None:
            self.status_lbl.setText("No image loaded.")
            return
        if self.active_style is None:
            self.status_lbl.setText("Select a style first.")
            return
        intensity = self.intensity_slider.value() / 100.0
        self.apply_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_lbl.setText("Applying...")
        self.worker = StyleWorker(
            self.editor.current.copy(), self.active_style, intensity
        )
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_finished(self, result):
        self.editor.save_state()
        self.editor.current = result.convert("RGBA")
        self.editor.base    = self.editor.current.copy()
        self.refresh()
        self.status_lbl.setText("Done!")
        self.apply_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

    def on_error(self, msg):
        self.status_lbl.setText(f"Error: {msg}")
        self.apply_btn.setEnabled(True)
        self.progress_bar.setVisible(False)