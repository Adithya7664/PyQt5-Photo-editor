from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QLabel, QSlider, QPushButton, QComboBox, QColorDialog, QInputDialog
)

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from ui.brush_preview import BrushPreview

class PaintPanel(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas=canvas
        self.brush_color=QColor(255, 0, 0)
        self.recent_colors = []
        self.build_ui()
        
    def build_ui(self):
        self.setStyleSheet("background-color: #1c1c2e;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(8)

        grid = QGridLayout()
        grid.setSpacing(4)
        
        lbl_size = QLabel("Brush Size")
        lbl_size.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl_size.setStyleSheet("color: #e0e0e0;")

        self.size_val = QLabel("10")
        self.size_val.setFont(QFont("Segoe UI", 11))
        self.size_val.setStyleSheet("color: #00d4aa;")
        self.size_val.setFixedWidth(30)
        
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setMinimum(1)
        self.size_slider.setMaximum(100)
        self.size_slider.setValue(10)
        self.size_slider.setFixedHeight(24)
        self.size_slider.setMaximumWidth(220)
        self.size_slider.setStyleSheet(self.slider_style())
        self.size_slider.valueChanged.connect(lambda v: self.size_val.setText(str(v)))
        self.size_slider.valueChanged.connect(self.update_brush)
        
        lbl_opacity=QLabel("Opacity")
        lbl_opacity.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl_opacity.setStyleSheet("color: #e0e0e0;")
        
        self.opacity_val = QLabel("100")
        self.opacity_val.setFont(QFont("Segoe UI", 11))
        self.opacity_val.setStyleSheet("color: #00d4aa;")
        self.opacity_val.setFixedWidth(30)
        
        self.opacity_slider=QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(1)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setFixedHeight(24)
        self.opacity_slider.setMaximumWidth(220)
        self.opacity_slider.setStyleSheet(self.slider_style())
        self.opacity_slider.valueChanged.connect(lambda v: self.opacity_val.setText(str(v)))
        self.opacity_slider.valueChanged.connect(self.update_brush)
        
        grid.addWidget(lbl_size,         0, 0)
        grid.addWidget(self.size_slider, 0, 1)
        grid.addWidget(self.size_val,    0, 2)
        grid.addWidget(lbl_opacity,         1, 0)
        grid.addWidget(self.opacity_slider, 1, 1)
        grid.addWidget(self.opacity_val,    1, 2)
        
        self.brush_preview = BrushPreview()
        
        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)
        top_layout.addLayout(grid)
        top_layout.addWidget(self.brush_preview, 1, Qt.AlignCenter)
        top_layout.addLayout(self.make_right_panel())

        main_layout.addLayout(top_layout, stretch=1)
        main_layout.addLayout(self.make_controls())
        
    def make_controls(self):
        layout=QHBoxLayout()
        layout.setSpacing(10)
        
        btn_style = """
              QPushButton {
                  background-color: #1c1c2e;
                  color: #00d4aa;
                  border: 1px solid #00d4aa;
                  border-radius: 4px;
                  padding: 10px;
                  font-size: 12pt;
              }
              QPushButton:hover {
                  background-color: #00d4aa;
                  color: #1a1a1a;
              }
              QPushButton:checked {
                  background-color: #00d4aa;
                  color: #1a1a1a;
              }
          """

        self.brush_btn = QPushButton("Brush")
        self.brush_btn.setCheckable(True)
        self.brush_btn.setChecked(True)
        self.brush_btn.setStyleSheet(btn_style)
        self.brush_btn.setMinimumWidth(100)
        self.brush_btn.setMaximumWidth(150)
        self.brush_btn.clicked.connect(self.activate_brush)

        self.eraser_btn = QPushButton("Eraser")
        self.eraser_btn.setCheckable(True)
        self.eraser_btn.setStyleSheet(btn_style)
        self.eraser_btn.setMinimumWidth(100)
        self.eraser_btn.setMaximumWidth(150)
        self.eraser_btn.clicked.connect(self.activate_eraser)
        
        self.text_btn = QPushButton("Text")
        self.text_btn.setCheckable(True)
        self.text_btn.setStyleSheet(btn_style)
        self.text_btn.setMinimumWidth(100)
        self.text_btn.setMaximumWidth(150)
        self.text_btn.clicked.connect(self.activate_text)
        
        self.eyedrop_btn = QPushButton("Eyedrop")
        self.eyedrop_btn.setCheckable(True)
        self.eyedrop_btn.setStyleSheet(btn_style)
        self.eyedrop_btn.setMinimumWidth(100)
        self.eyedrop_btn.setMaximumWidth(150)
        self.eyedrop_btn.clicked.connect(self.activate_eyedrop)
        
        self.color_btn = QPushButton("Color")
        self.color_btn.setStyleSheet(btn_style + "QPushButton { background-color: #ff0000; color: #ffffff; border: 1px solid #ff0000; }")
        self.color_btn.setMinimumWidth(100)
        self.color_btn.setMaximumWidth(150)
        self.color_btn.clicked.connect(self.pick_color)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Round", "Square", "Soft"])
        self.type_combo.setStyleSheet("""
            QComboBox {
                background-color: #1c1c2e;
                color: #00d4aa;
                border: 1px solid #00d4aa;
                border-radius: 4px;
                padding: 8px;
                font-size: 12pt;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #1c1c2e;
                color: #e0e0e0;
                selection-background-color: #00d4aa;
                selection-color: #1a1a1a;
            }
        """)
        self.type_combo.setMinimumWidth(100)
        self.type_combo.setMaximumWidth(150)
        self.type_combo.currentTextChanged.connect(self.update_brush)

        layout.addWidget(self.brush_btn)
        layout.addWidget(self.eraser_btn)
        layout.addWidget(self.color_btn)
        layout.addWidget(self.type_combo)
        layout.addWidget(self.eyedrop_btn)
        layout.addWidget(self.text_btn)

        return layout
    
    def slider_style(self):
        return """
            QSlider::groove:horizontal {
                height: 5px;
                background: #252540;
                border-radius: 2px;
                border: 1px solid #333355;
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
        
    def activate_brush(self):
        self.eraser_btn.setChecked(False)
        self.eyedrop_btn.setChecked(False)
        self.text_btn.setChecked(False)
        self.brush_btn.setChecked(True)
        self.canvas.set_mode("paint")
        self.update_brush()
        
    def activate_eraser(self):
        self.brush_btn.setChecked(False)
        self.text_btn.setChecked(False)
        self.eraser_btn.setChecked(True)
        self.canvas.set_mode("erase")
        self.update_brush()

    def pick_color(self):
        color = QColorDialog.getColor(self.brush_color, self)
        if color.isValid():
            self.brush_color = color
            self.add_recent_color(color)
            self.color_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color.name()};
                    color: #ffffff;
                    border: 1px solid {color.name()};
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 12pt;
                }}
            """)
            self.update_brush()
    
    def update_brush(self):
        size    = self.size_slider.value()
        opacity = self.opacity_slider.value()
        btype   = self.type_combo.currentText().lower()
        self.canvas.update_brush(size, self.brush_color, opacity, btype)
        self.brush_preview.update_brush(size, self.brush_color, opacity, btype)
        
    def activate_eyedrop(self):
        self.brush_btn.setChecked(False)
        self.eraser_btn.setChecked(False)
        self.eyedrop_btn.setChecked(True)
        self.canvas.set_mode("eyedrop")
        try:
            self.canvas.color_picked.disconnect(self.on_color_picked)
        except TypeError:
            pass
        self.canvas.color_picked.connect(self.on_color_picked)
    
    def on_color_picked(self, color):
        self.brush_color = color
        self.add_recent_color(color)
        self.color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color.name()};
                color: #ffffff;
                border: 1px solid {color.name()};
                border-radius: 4px;
                padding: 8px;
                font-size: 12pt;
            }}
        """)
        self.activate_brush()
        
    def make_right_panel(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Recent colors
        rc_label = QLabel("Recent Colors")
        rc_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        rc_label.setStyleSheet("color: #888888;")
        layout.addWidget(rc_label)

        swatch_layout = QHBoxLayout()
        swatch_layout.setSpacing(4)
        self.color_swatches = []
        for i in range(8):
            btn = QPushButton()
            btn.setFixedSize(24, 24)
            btn.setStyleSheet("background-color: #2a2a2a; border: 1px solid #444; border-radius: 3px;")
            btn.clicked.connect(lambda _, idx=i: self.apply_swatch(idx))
            swatch_layout.addWidget(btn)
            self.color_swatches.append(btn)
        swatch_layout.addStretch()
        layout.addLayout(swatch_layout)

        # Symmetry
        sym_label = QLabel("Symmetry")
        sym_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        sym_label.setStyleSheet("color: #888888;")
        layout.addWidget(sym_label)

        sym_layout = QHBoxLayout()
        sym_layout.setSpacing(6)
        btn_style = """
            QPushButton { background-color: #1c1c2e; color: #00d4aa;
                border: 1px solid #00d4aa; border-radius: 4px; padding: 5px 12px; font-size: 10pt; }
            QPushButton:checked { background-color: #00d4aa; color: #1a1a1a; }
            QPushButton:hover { background-color: #00d4aa; color: #1a1a1a; }
        """
        self.sym_h_btn = QPushButton("↔  H")
        self.sym_h_btn.setCheckable(True)
        self.sym_h_btn.setStyleSheet(btn_style)
        self.sym_h_btn.toggled.connect(self.canvas.set_symmetry_h)

        self.sym_v_btn = QPushButton("↕  V")
        self.sym_v_btn.setCheckable(True)
        self.sym_v_btn.setStyleSheet(btn_style)
        self.sym_v_btn.toggled.connect(self.canvas.set_symmetry_v)

        sym_layout.addWidget(self.sym_h_btn)
        sym_layout.addWidget(self.sym_v_btn)
        sym_layout.addStretch()
        layout.addLayout(sym_layout)

        layout.addStretch()
        return layout
    
    def add_recent_color(self, color):
        if not self.color_swatches:
            return
        for c in self.color_swatches:
            if c.property("color") == color.name():
                return
        self.recent_colors.insert(0, color)
        if len(self.recent_colors) > 8:
            self.recent_colors.pop()
        for i, c in enumerate(self.recent_colors):
            self.color_swatches[i].setStyleSheet(
                f"background-color: {c.name()}; border: 1px solid #666; border-radius: 3px;")
            self.color_swatches[i].setProperty("color", c.name())
            
    def apply_swatch(self, idx):
        if idx < len(self.recent_colors):
            self.brush_color = self.recent_colors[idx]
            self.color_btn.setStyleSheet(f"""
                QPushButton {{ background-color: {self.brush_color.name()};
                    color: #ffffff; border: 1px solid {self.brush_color.name()};
                    border-radius: 4px; padding: 8px; font-size: 12pt; }}
            """)
            self.update_brush()
            
    def activate_text(self):
        self.brush_btn.setChecked(False)
        self.eraser_btn.setChecked(False)
        self.eyedrop_btn.setChecked(False)
        self.text_btn.setChecked(True)
        self.canvas.set_mode("text")
        try:
            self.canvas.text_clicked.disconnect(self.on_text_clicked)
        except TypeError:
            pass
        self.canvas.text_clicked.connect(self.on_text_clicked)

    def on_text_clicked(self, pt):
        text, ok = QInputDialog.getText(self, "Add Text", "Enter text:")
        if ok and text.strip():
            font_size = max(8, self.size_slider.value() // 2)
            self.canvas.draw_text(pt, text.strip(), font_size, self.brush_color, self.opacity_slider.value())
