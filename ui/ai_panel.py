from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QSlider, QCheckBox, QProgressBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ai_pipeline import AIWorker

class AIPanel(QWidget):
    def __init__(self, editor, refresh_callback):
        super().__init__()
        self.editor  = editor
        self.refresh = refresh_callback
        self.worker  = None
        self.build_ui()

    def build_ui(self):
        self.setStyleSheet("background-color: #1c1c2e;")
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 8, 16, 8)
        main_layout.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(6)

        lbl = QLabel("Prompt")
        lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        lbl.setStyleSheet("color: #888888;")
        left.addWidget(lbl)

        self.prompt_box = QTextEdit()
        self.prompt_box.setPlaceholderText("e.g. make it look like sunset, add snow, make it look like a painting")
        self.prompt_box.setFixedHeight(55)
        self.prompt_box.setStyleSheet("""
            QTextEdit {
                background-color: #13132a; color: #e0e0e0;
                border: 1px solid #00d4aa; border-radius: 4px;
                padding: 4px; font-size: 10pt;
            }
        """)
        left.addWidget(self.prompt_box)

        left.addLayout(self.make_slider("Steps",          "steps",        10, 50,  20, integer=True))
        left.addLayout(self.make_slider("Image Guidance", "img_guidance", 10, 30,  15))
        left.addLayout(self.make_slider("Text Guidance",  "txt_guidance", 50, 150, 75))

        checks = QHBoxLayout()
        self.gfpgan_check = self.make_checkbox("Enhance Faces (GFPGAN)")
        self.esrgan_check = self.make_checkbox("Upscale 4x (Real-ESRGAN)")
        checks.addWidget(self.gfpgan_check)
        checks.addWidget(self.esrgan_check)
        checks.addStretch()
        left.addLayout(checks)
        left.addStretch()
        main_layout.addLayout(left, stretch=2)

        right = QVBoxLayout()
        right.setSpacing(8)

        self.generate_btn = QPushButton("✦  Generate")
        self.generate_btn.setFixedHeight(42)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d4aa; color: #1a1a1a;
                border: none; border-radius: 6px;
                font-size: 12pt; font-weight: bold;
            }
            QPushButton:hover    { background-color: #00ffcc; }
            QPushButton:disabled { background-color: #2a2a2a; color: #555555; }
        """)
        self.generate_btn.clicked.connect(self.generate)
        right.addWidget(self.generate_btn)

        self.status_lbl = QLabel("Load an image and enter a prompt")
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

    def make_slider(self, label, key, mn, mx, default, integer=False):
        row = QHBoxLayout()
        row.setSpacing(6)
        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 9))
        lbl.setStyleSheet("color: #cccccc;")
        lbl.setFixedWidth(105)
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(mn)
        slider.setMaximum(mx)
        slider.setValue(default)
        slider.setFixedHeight(20)
        slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #252540; border-radius: 2px; }
            QSlider::handle:horizontal { background: #00d4aa; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }
            QSlider::sub-page:horizontal { background: #00d4aa; border-radius: 2px; }
        """)
        val_lbl = QLabel(str(default) if integer else str(round(default / 10, 1)))
        val_lbl.setStyleSheet("color: #00d4aa; font-size: 9pt;")
        val_lbl.setFixedWidth(32)
        val_lbl.setAlignment(Qt.AlignCenter)
        if integer:
            slider.valueChanged.connect(lambda v, l=val_lbl: l.setText(str(v)))
        else:
            slider.valueChanged.connect(lambda v, l=val_lbl: l.setText(str(round(v / 10, 1))))
        setattr(self, f"{key}_slider", slider)
        row.addWidget(lbl)
        row.addWidget(slider)
        row.addWidget(val_lbl)
        return row

    def make_checkbox(self, text):
        cb = QCheckBox(text)
        cb.setStyleSheet("""
            QCheckBox { color: #cccccc; font-size: 9pt; }
            QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid #00d4aa; border-radius: 3px; background: #13132a; }
            QCheckBox::indicator:checked { background: #00d4aa; }
        """)
        return cb

    def generate(self):
        if self.editor.current is None:
            self.status_lbl.setText("No image loaded.")
            return
        prompt = self.prompt_box.toPlainText().strip()
        if not prompt:
            self.status_lbl.setText("Enter a prompt first.")
            return
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.worker = AIWorker(
            image=self.editor.current,
            prompt=prompt,
            steps=self.steps_slider.value(),
            img_guidance=self.img_guidance_slider.value() / 10,
            txt_guidance=self.txt_guidance_slider.value() / 10,
            use_gfpgan=self.gfpgan_check.isChecked(),
            use_esrgan=self.esrgan_check.isChecked()
        )
        self.worker.progress.connect(self.status_lbl.setText)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_finished(self, result):
        self.editor.save_state()
        self.editor.current = result.convert("RGBA")
        self.editor.base    = self.editor.current.copy()
        self.refresh()
        self.status_lbl.setText("Done! Image updated.")
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

    def on_error(self, msg):
        self.status_lbl.setText(f"Error: {msg}")
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)