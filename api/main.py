import base64
import io
import sys
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

app = FastAPI()

class StyleRequest(BaseModel):
    image:     str
    style:     str
    intensity: float = 1.0

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/apply-style")
def apply_style(req: StyleRequest):
    from styles.style_engine import (
        apply_sketch, apply_cartoon, apply_watercolor, apply_oil,
        apply_sepia, apply_fade, apply_vivid, apply_cinematic,
        apply_bw, apply_anime, apply_starry, apply_mosaic,
        apply_candy, apply_rain
    )
    fns = {
        "sketch":     apply_sketch,
        "cartoon":    apply_cartoon,
        "watercolor": apply_watercolor,
        "oil":        apply_oil,
        "sepia":      apply_sepia,
        "fade":       apply_fade,
        "vivid":      apply_vivid,
        "cinematic":  apply_cinematic,
        "bw":         apply_bw,
        "anime":      apply_anime,
        "starry":     apply_starry,
        "mosaic":     apply_mosaic,
        "candy":      apply_candy,
        "rain":       apply_rain,
    }
    if req.style not in fns:
        raise HTTPException(status_code=400, detail=f"Unknown style: {req.style}")
    try:
        img_bytes = base64.b64decode(req.image)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        result = fns[req.style](img, req.intensity)
        buf = io.BytesIO()
        result.convert("RGB").save(buf, format="PNG")
        encoded = base64.b64encode(buf.getvalue()).decode()
        return {"image": encoded}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))