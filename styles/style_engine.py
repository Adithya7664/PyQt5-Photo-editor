from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np
import os
import torch

def _models_dir():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

def _blend(original, result, intensity):
    return Image.blend(original.convert("RGB"), result.convert("RGB"), intensity)


# ── Instant styles ────────────────────────────────────────────────────────────

def apply_sketch(img, intensity=1.0):
    gray     = img.convert("L")
    inverted = ImageOps.invert(gray)
    blurred  = inverted.filter(ImageFilter.GaussianBlur(radius=21))
    g = np.array(gray,    dtype=np.float32)
    b = np.array(blurred, dtype=np.float32)
    sketch = np.clip(g * 255.0 / (255.0 - b + 1e-6), 0, 255).astype(np.uint8)
    result = Image.fromarray(sketch).convert("RGB")
    return _blend(img, result, intensity)

def apply_cartoon(img, intensity=1.0):
    import cv2
    arr = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)
    for _ in range(3):
        arr = cv2.bilateralFilter(arr, 9, 75, 75)
    gray  = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
    gray  = cv2.medianBlur(gray, 7)
    edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                    cv2.THRESH_BINARY, 9, 9)
    cartoon = cv2.bitwise_and(arr, arr, mask=edges)
    result  = Image.fromarray(cv2.cvtColor(cartoon, cv2.COLOR_BGR2RGB))
    return _blend(img, result, intensity)

def apply_watercolor(img, intensity=1.0):
    import cv2
    # Step 1: quantize colors to flat paint-like areas
    small = img.convert("RGB").resize((img.width // 2, img.height // 2))
    quantized = small.quantize(colors=48).convert("RGB")
    quantized = quantized.resize(img.size, Image.BILINEAR)

    # Step 2: blur slightly to simulate paint bleeding at edges
    quantized = quantized.filter(ImageFilter.GaussianBlur(radius=1.5))

    # Step 3: slight desaturation and brightness lift (paint transparency)
    quantized = ImageEnhance.Color(quantized).enhance(0.85)
    quantized = ImageEnhance.Brightness(quantized).enhance(1.1)

    # Step 4: soft edge overlay from original
    bgr = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 180)
    edges = cv2.GaussianBlur(edges.astype(np.float32), (3, 3), 0) / 255.0
    arr = np.array(quantized, dtype=np.float32)
    for c in range(3):
        arr[:, :, c] *= (1.0 - edges * 0.5)
    result = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return _blend(img, result, intensity)

def apply_oil(img, intensity=1.0):
    result = img.filter(ImageFilter.MedianFilter(size=5))
    result = result.filter(ImageFilter.MedianFilter(size=3))
    result = ImageEnhance.Contrast(result).enhance(1.2)
    result = ImageEnhance.Color(result).enhance(1.3)
    result = result.filter(ImageFilter.EDGE_ENHANCE)
    return _blend(img, result, intensity)

def apply_sepia(img, intensity=1.0):
    arr     = np.array(img.convert("RGB"), dtype=np.float32)
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    ro = np.clip(r*0.393 + g*0.769 + b*0.189, 0, 255)
    go = np.clip(r*0.349 + g*0.686 + b*0.168, 0, 255)
    bo = np.clip(r*0.272 + g*0.534 + b*0.131, 0, 255)
    result = Image.fromarray(np.stack([ro, go, bo], axis=2).astype(np.uint8))
    return _blend(img, result, intensity)

def apply_fade(img, intensity=1.0):
    result = img.point(lambda i: int(i * 0.75 + 50))
    result = ImageEnhance.Color(result).enhance(0.7)
    return _blend(img, result, intensity)

def apply_vivid(img, intensity=1.0):
    result = ImageEnhance.Color(img).enhance(1.6)
    result = ImageEnhance.Contrast(result).enhance(1.2)
    result = ImageEnhance.Brightness(result).enhance(1.05)
    return _blend(img, result, intensity)

def apply_cinematic(img, intensity=1.0):
    arr     = np.array(img.convert("RGB"), dtype=np.float32)
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    lum       = 0.299*r + 0.587*g + 0.114*b
    shadow    = np.clip(1 - lum / 128, 0, 1)
    highlight = np.clip(lum / 128 - 1, 0, 1)
    r = r - shadow*15 + highlight*20
    g = g + shadow*5  + highlight*10
    b = b + shadow*20 - highlight*15
    result = Image.fromarray(np.clip(np.stack([r, g, b], axis=2), 0, 255).astype(np.uint8))
    result = ImageEnhance.Contrast(result).enhance(1.2)
    return _blend(img, result, intensity)

def apply_bw(img, intensity=1.0):
    arr  = np.array(img.convert("RGB"), dtype=np.float32)
    gray = np.clip(arr[:,:,0]*0.299 + arr[:,:,1]*0.587 + arr[:,:,2]*0.114, 0, 255).astype(np.uint8)
    result = Image.fromarray(np.stack([gray, gray, gray], axis=2))
    return _blend(img, result, intensity)


# ── Neural: Anime/Ghibli ──────────────────────────────────────────────────────

_anime_model = None

def apply_anime(img, intensity=1.0):
    global _anime_model
    if _anime_model is None:
        _anime_model = torch.hub.load(
            'bryandlee/animegan2-pytorch:main', 'generator',
            pretrained='paprika', progress=True
        ).eval()
    orig_size = img.size  # save original (W, H)
    w, h = orig_size
    w32 = w - w % 32
    h32 = h - h % 32
    resized = img.convert("RGB").resize((512, 512))
    arr    = np.array(resized, dtype=np.float32) / 127.5 - 1.0
    tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)
    with torch.no_grad():
        out = _anime_model(tensor).squeeze(0).permute(1, 2, 0).detach().numpy()
    result = Image.fromarray(np.clip((out + 1.0) * 127.5, 0, 255).astype(np.uint8))
    result = result.resize(orig_size)  # restore original size
    return _blend(img, result, intensity)


# ── Neural: Fast NST (TransformerNet) ────────────────────────────────────────

class _ConvLayer(torch.nn.Module):
    def __init__(self, in_ch, out_ch, k, s):
        super().__init__()
        self.reflection_pad = torch.nn.ReflectionPad2d(k // 2)
        self.conv2d = torch.nn.Conv2d(in_ch, out_ch, k, s)
    def forward(self, x): return self.conv2d(self.reflection_pad(x))

class _ResBlock(torch.nn.Module):
    def __init__(self, ch):
        super().__init__()
        self.conv1 = _ConvLayer(ch, ch, 3, 1)
        self.in1   = torch.nn.InstanceNorm2d(ch, affine=True)
        self.conv2 = _ConvLayer(ch, ch, 3, 1)
        self.in2   = torch.nn.InstanceNorm2d(ch, affine=True)
        self.relu  = torch.nn.ReLU()
    def forward(self, x):
        return self.in2(self.conv2(self.relu(self.in1(self.conv1(x))))) + x

class _UpsampleConv(torch.nn.Module):
    def __init__(self, in_ch, out_ch, k, s, up):
        super().__init__()
        self.upsample       = up
        self.reflection_pad = torch.nn.ReflectionPad2d(k // 2)
        self.conv2d         = torch.nn.Conv2d(in_ch, out_ch, k, s)
    def forward(self, x):
        if self.upsample:
            x = torch.nn.functional.interpolate(x, scale_factor=self.upsample, mode='nearest')
        return self.conv2d(self.reflection_pad(x))

class _TransformerNet(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1   = _ConvLayer(3,   32,  9, 1)
        self.in1     = torch.nn.InstanceNorm2d(32,  affine=True)
        self.conv2   = _ConvLayer(32,  64,  3, 2)
        self.in2     = torch.nn.InstanceNorm2d(64,  affine=True)
        self.conv3   = _ConvLayer(64,  128, 3, 2)
        self.in3     = torch.nn.InstanceNorm2d(128, affine=True)
        self.res1    = _ResBlock(128)
        self.res2    = _ResBlock(128)
        self.res3    = _ResBlock(128)
        self.res4    = _ResBlock(128)
        self.res5    = _ResBlock(128)
        self.deconv1 = _UpsampleConv(128, 64, 3, 1, 2)
        self.in4     = torch.nn.InstanceNorm2d(64,  affine=True)
        self.deconv2 = _UpsampleConv(64,  32, 3, 1, 2)
        self.in5     = torch.nn.InstanceNorm2d(32,  affine=True)
        self.deconv3 = _ConvLayer(32, 3, 9, 1)
        self.relu    = torch.nn.ReLU()
    def forward(self, x):
        y = self.relu(self.in1(self.conv1(x)))
        y = self.relu(self.in2(self.conv2(y)))
        y = self.relu(self.in3(self.conv3(y)))
        y = self.res1(y); y = self.res2(y); y = self.res3(y)
        y = self.res4(y); y = self.res5(y)
        y = self.relu(self.in4(self.deconv1(y)))
        y = self.relu(self.in5(self.deconv2(y)))
        return self.deconv3(y)

_nst_cache = {}

def _run_nst(img, filename, intensity):
    path = os.path.join(_models_dir(), filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Model not found: {path} — download '{filename}' from the PyTorch "
            f"fast-neural-style examples and place it in the models/ folder."
        )
    if filename not in _nst_cache:
        net   = _TransformerNet()
        state = torch.load(path, map_location='cpu')
        for k in list(state.keys()):
            if 'running_mean' in k or 'running_var' in k:
                del state[k]
        net.load_state_dict(state)
        net.eval()
        _nst_cache[filename] = net
    net    = _nst_cache[filename]
    arr    = np.array(img.convert("RGB"), dtype=np.float32)
    tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)
    with torch.no_grad():
        out = net(tensor).squeeze(0).clamp(0, 255)
    result = Image.fromarray(out.byte().permute(1, 2, 0).numpy())
    return _blend(img, result, intensity)

def apply_starry(img, intensity=1.0): return _run_nst(img, "starry_night.pth", intensity)
def apply_mosaic(img, intensity=1.0): return _run_nst(img, "mosaic.pth",       intensity)
def apply_candy(img,  intensity=1.0): return _run_nst(img, "candy.pth",         intensity)
def apply_rain(img,   intensity=1.0): return _run_nst(img, "rain_princess.pth", intensity)