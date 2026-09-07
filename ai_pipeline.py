import torch
import os
import numpy as np
from PIL import Image
from PyQt5.QtCore import QThread, pyqtSignal

def get_device():
    if torch.cuda.is_available():
        return "cuda"
    try:
        import torch_directml
        return torch_directml.device()
    except:
        return "cpu"

_device = get_device()
_ip2p_pipe = None
_gfpganer = None
_esrganer = None
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

def load_ip2p():
    global _ip2p_pipe
    if _ip2p_pipe is None:
        from diffusers import StableDiffusionInstructPix2PixPipeline
        dtype = torch.float16 if str(_device) == "cuda" else torch.float32
        _ip2p_pipe = StableDiffusionInstructPix2PixPipeline.from_pretrained(
            "timbrooks/instruct-pix2pix",
            torch_dtype=dtype,
            safety_checker=None
        ).to("cpu")
        _ip2p_pipe.enable_attention_slicing()
    return _ip2p_pipe

def load_gfpgan():
    global _gfpganer
    if _gfpganer is None:
        from gfpgan import GFPGANer
        model_path = os.path.join(MODELS_DIR, "GFPGANv1.4.pth")
        _gfpganer = GFPGANer(
            model_path=model_path, upscale=1,
            arch='clean', channel_multiplier=2, bg_upsampler=None
        )
    return _gfpganer

def load_esrgan():
    global _esrganer
    if _esrganer is None:
        from realesrgan import RealESRGANer
        from basicsr.archs.rrdbnet_arch import RRDBNet
        model_path = os.path.join(MODELS_DIR, "RealESRGAN_x4plus.pth")
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
                        num_block=23, num_grow_ch=32, scale=4)
        _esrganer = RealESRGANer(scale=4, model_path=model_path,
                                model=model, tile=400, tile_pad=10,
                                pre_pad=0, half=False)
    return _esrganer


class AIWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)
    error    = pyqtSignal(str)

    def __init__(self, image, prompt, steps, img_guidance, txt_guidance, use_gfpgan, use_esrgan):
        super().__init__()
        self.image        = image
        self.prompt       = prompt
        self.steps        = steps
        self.img_guidance = img_guidance
        self.txt_guidance = txt_guidance
        self.use_gfpgan   = use_gfpgan
        self.use_esrgan   = use_esrgan

    def run(self):
        try:
            os.makedirs(MODELS_DIR, exist_ok=True)

            self.progress.emit("Loading InstructPix2Pix (first run downloads ~6GB)...")
            pipe = load_ip2p()

            self.progress.emit(f"Generating: '{self.prompt}'...")
            img = self.image.convert("RGB").resize((512, 512))
            result = pipe(
                prompt=self.prompt,
                image=img,
                num_inference_steps=self.steps,
                image_guidance_scale=self.img_guidance,
                guidance_scale=self.txt_guidance
            ).images[0]

            if self.use_gfpgan:
                self.progress.emit("Enhancing faces with GFPGAN...")
                try:
                    arr = np.array(result)[:, :, ::-1]
                    _, _, enhanced = load_gfpgan().enhance(
                        arr, has_aligned=False, only_center_face=False, paste_back=True)
                    result = Image.fromarray(enhanced[:, :, ::-1])
                except Exception as e:
                    self.progress.emit(f"GFPGAN skipped: {e}")

            if self.use_esrgan:
                self.progress.emit("Upscaling 4x with Real-ESRGAN...")
                try:
                    arr = np.array(result)[:, :, ::-1]
                    enhanced, _ = load_esrgan().enhance(arr, outscale=4)
                    result = Image.fromarray(enhanced[:, :, ::-1])
                except Exception as e:
                    self.progress.emit(f"Real-ESRGAN skipped: {e}")

            self.progress.emit("Done!")
            self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))