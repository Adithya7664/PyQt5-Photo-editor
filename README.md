# GenPhoto — Desktop Photo Editor

A dark-themed desktop photo editor built with PyQt5 and PIL, featuring non-destructive adjustments, a full paint toolkit, AI-powered style transfer, and one-click background removal.

---

## Download

> **[Download GenPhoto.exe](https://github.com/Adithya7664/PyQt5-Photo-editor/releases/latest)**

No installation required — double-click and run. Windows only.

> First launch takes 15–30 seconds while the app unpacks dependencies.

---

## Features

### Basic Adjustments
Three-tab panel with a live histogram that updates in real time.

| Tab | Controls |
|-----|----------|
| **Tone** | Brightness, Contrast, Exposure, Highlights, Shadows |
| **Color** | Saturation, Vibrance, Temperature, Hue |
| **Detail** | Sharpness, Blur, Vignette |

Additional tools in the Basic panel:

- **Rotate 90°** — non-destructive rotation
- **Flip H / Flip V** — horizontal and vertical mirror
- **Crop** — drag a selection on the canvas, applies instantly
- **Remove BG** — one-click background removal powered by [rembg](https://github.com/danielgatis/rembg)
- **Auto Enhance** — automatic contrast + color + brightness boost in one click

### Paint
Full painting overlay that sits on top of the photo without destroying it.

| Tool | Description |
|------|-------------|
| **Brush** | Round, Square, or Soft tip — adjustable size (1–100) and opacity (1–100) |
| **Eraser** | Erases paint strokes without touching the photo below |
| **Eyedropper** | Click any pixel on the canvas to pick its colour |
| **Text** | Click anywhere on the canvas, type text — rendered in the current brush colour and size |
| **Color Picker** | Full colour dialog; recent colours strip stores the last 8 used |
| **Symmetry** | Horizontal and vertical mirror painting modes |
| **Brush Preview** | Live 120×120 preview widget showing exactly how the brush will look |

### Styles
14 styles in two categories. Each style has an **Intensity** slider (0–100).

**Instant styles** — run fully in-process, apply in under a second:

| Style | Effect |
|-------|--------|
| Pencil Sketch | Dodge-blend grayscale pencil look |
| Cartoon | Bilateral filter + adaptive edge outlines |
| Watercolor | Color quantization + soft edge overlay |
| Oil Painting | Median filter stack + edge enhancement |
| Sepia | Classic warm sepia tone matrix |
| Fade | Lifted shadows + desaturated film fade |
| Vivid | Boosted saturation, contrast, and brightness |
| Cinematic | Teal-shadow / orange-highlight colour grade |
| B&W | Luminosity-weighted monochrome conversion |

**Neural styles** — require downloaded model files (see below), run on CPU:

| Style | Model file |
|-------|-----------|
| Anime / Ghibli *(experimental, output quality unreliable)* | AnimeGAN2 (`paprika` weights, auto-downloaded via torch.hub) |
| Starry Night | `starry_night.pth` |
| Mosaic | `mosaic.pth` |
| Candy | `candy.pth` |
| Rain Princess | `rain_princess.pth` |

### Canvas
- **Zoom** — scroll wheel to zoom in/out
- **Pan** — right-click drag to pan around the image
- **Before/After** — hold the **Before/After** button in the toolbar to instantly compare the original; release to return to the edited version

### File & History
- Open: PNG, JPG, JPEG, BMP, WEBP
- Save: PNG or JPEG (95% quality)
- **Recent Files** — last 5 opened files listed under File → Recent Files
- **Undo** (`Ctrl+Z`) — up to 20 steps
- **Reset** (`Ctrl+R`) — reverts to the original image

---

## Running from source

### 1. Clone

```bash
git clone https://github.com/Adithya7664/PyQt5-Photo-editor.git
cd PyQt5-Photo-editor
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install PyQt5 pillow numpy opencv-python rembg torch torchvision
```

### 3. Run

```bash
python main.py
```

---

## Neural style models

The experimental Anime / Ghibli style downloads its weights automatically on first use via `torch.hub`; its results are not consistently good, unlike the other styles.

For the four fast-NST styles (Starry Night, Mosaic, Candy, Rain Princess), download the `.pth` files from the [PyTorch fast-neural-style examples](https://github.com/pytorch/examples/tree/main/fast_neural_style) and place them in a `models/` folder in the project root:

```
models/
├── starry_night.pth
├── mosaic.pth
├── candy.pth
└── rain_princess.pth
```

The app shows an error for those styles if the files are missing — all other styles and features work without them.

---

## Project structure

```
├── main.py                  # Entry point
├── editor.py                # Non-destructive image operations
├── Dockerfile               # FastAPI style server (optional, for server deployment)
├── requirements_api.txt     # API server dependencies
├── api/
│   └── main.py              # FastAPI style endpoint
├── styles/
│   └── style_engine.py      # All 14 style implementations
└── ui/
    ├── main_window.py        # Main window, toolbar, layout
    ├── basic_panel.py        # Tone/Color/Detail sliders + histogram
    ├── paint_panel.py        # Paint tools panel
    ├── style_panel.py        # Style selection UI + worker thread
    ├── zoom_canvas.py        # Zoomable/pannable canvas with paint overlay
    ├── brush_preview.py      # Live brush preview widget
    ├── histogram.py          # RGB histogram widget
    └── canvas.py             # Base canvas widget
```

---

## Tech stack

| Layer | Library |
|-------|---------|
| UI | PyQt5 |
| Image processing | Pillow, NumPy, OpenCV |
| Neural styles | PyTorch, AnimeGAN2 |
| Background removal | rembg (U²-Net) |

---

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open image |
| `Ctrl+S` | Save image |
| `Ctrl+Z` | Undo |
| `Ctrl+R` | Reset to original |
| `Ctrl+Q` | Quit |
