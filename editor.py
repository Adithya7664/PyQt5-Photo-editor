from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import rembg
import io

class editor:
    def __init__(self):
        self.original = None
        self.current = None
        self.history = []
        
    def load(self, file_path):
        self.original = Image.open(file_path).convert("RGBA")
        self.current = self.original.copy()
        self.history = [self.current.copy()]
        self.base = self.current.copy()

    def save_state(self):
        self.history.append(self.current.copy())
        if len(self.history) > 20:
            self.history.pop(0)

    def undo(self):
        if len(self.history) > 1:
            self.history.pop()
            self.current = self.history[-1].copy()
        return self.current
    
    def adjust_brightness(self, value):
          self.save_state()
          self.current = ImageEnhance.Brightness(self.current).enhance(value)
          return self.current

    def adjust_contrast(self, value):
        self.save_state()
        self.current = ImageEnhance.Contrast(self.current).enhance(value)
        return self.current

    def adjust_saturation(self, value):
        self.save_state()
        self.current = ImageEnhance.Color(self.current).enhance(value)
        return self.current

    def adjust_sharpness(self, value):
        self.save_state()
        self.current = ImageEnhance.Sharpness(self.current).enhance(value)
        return self.current
    
    def rotate(self, degrees):
          self.save_state()
          self.current = self.current.rotate(degrees, expand=True)
          self.base = self.current.copy()
          return self.current

    def flip_horizontal(self):
        self.save_state()
        self.current = self.current.transpose(Image.FLIP_LEFT_RIGHT)
        self.base = self.current.copy()
        return self.current

    def flip_vertical(self):
        self.save_state()
        self.current = self.current.transpose(Image.FLIP_TOP_BOTTOM)
        self.base = self.current.copy()
        return self.current

    def crop(self, left, top, right, bottom):
        self.save_state()
        self.current = self.current.crop((left, top, right, bottom))
        self.base = self.current.copy()
        return self.current

    def remove_background(self):
        self.save_state()
        buffer=io.BytesIO()
        self.current.save(buffer, format="PNG")
        output = rembg.remove(buffer.getvalue())
        self.current = Image.open(io.BytesIO(output)).convert("RGBA")
        self.base = self.current.copy()
        return self.current
    
    def save(self, file_path):
        if file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
            self.current.convert("RGB").save(file_path, quality=95)
        else:
            self.current.save(file_path)

    def reset(self):
        self.current = self.original.copy()
        self.base = self.original.copy()
        self.history = [self.current.copy()]
        return self.current
    
    def apply_adjustments(self, brightness, contrast, saturation, sharpness,
                         temperature=0, exposure=0, highlights=0, shadows=0,
                         vibrance=0, hue=0, blur=0, vignette=0):
        img = self.base.copy()
        img = ImageEnhance.Brightness(img).enhance(brightness)
        img = ImageEnhance.Contrast(img).enhance(contrast)
        img = ImageEnhance.Color(img).enhance(saturation)
        img = ImageEnhance.Sharpness(img).enhance(sharpness)
        if temperature != 0:
            r, g, b, a = img.split()
            shift = int(abs(temperature) * 0.3)
            if temperature > 0:
                r = r.point(lambda i: min(255, i + shift))
                b = b.point(lambda i: max(0, i - shift))
            else:
                r = r.point(lambda i: max(0, i - shift))
                b = b.point(lambda i: min(255, i + shift))
            img = Image.merge("RGBA", (r, g, b, a))
        if exposure != 0:
            img = img.point(lambda i: max(0, min(255, i * (2 ** exposure))))
        if highlights != 0:
            img = img.point(lambda i: max(0, min(255, i + int(highlights * (i / 255)))))
        if shadows != 0:
            img = img.point(lambda i: max(0, min(255, i + int(shadows * (1 - i / 255)))))
        if vibrance != 0:
            rgb = img.convert("RGB")
            arr = np.array(rgb, dtype=np.float32)
            r_ch, g_ch, b_ch = arr[:,:,0], arr[:,:,1], arr[:,:,2]
            max_rgb = np.maximum(np.maximum(r_ch, g_ch), b_ch)
            min_rgb = np.minimum(np.minimum(r_ch, g_ch), b_ch)
            sat = (max_rgb - min_rgb) / (max_rgb + 1e-6)
            factor = 1 + vibrance * (1 - sat)
            avg = (r_ch + g_ch + b_ch) / 3
            arr[:,:,0] = np.clip(avg + factor * (r_ch - avg), 0, 255)
            arr[:,:,1] = np.clip(avg + factor * (g_ch - avg), 0, 255)
            arr[:,:,2] = np.clip(avg + factor * (b_ch - avg), 0, 255)
            result_rgb = Image.fromarray(arr.astype(np.uint8), 'RGB')
            _, _, _, a = img.split()
            r2, g2, b2 = result_rgb.split()
            img = Image.merge("RGBA", (r2, g2, b2, a))
        if hue != 0:
            rgb = img.convert("RGB")
            arr = np.array(rgb, dtype=np.float32) / 255.0
            r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
            maxc = np.maximum(np.maximum(r, g), b)
            minc = np.minimum(np.minimum(r, g), b)
            v = maxc
            s = np.where(maxc != 0, (maxc - minc) / maxc, 0)
            delta = maxc - minc
            h = np.zeros_like(v)
            mask = delta != 0
            rm = mask & (maxc == r)
            h[rm] = ((g[rm] - b[rm]) / delta[rm]) % 6
            gm = mask & (maxc == g)
            h[gm] = (b[gm] - r[gm]) / delta[gm] + 2
            bm = mask & (maxc == b)
            h[bm] = (r[bm] - g[bm]) / delta[bm] + 4
            h = (h / 6.0 + hue / 360.0) % 1.0
            h6 = h * 6.0
            i_idx = np.floor(h6).astype(int) % 6
            f = h6 - np.floor(h6)
            p = v * (1 - s)
            q = v * (1 - s * f)
            t = v * (1 - s * (1 - f))
            out = np.zeros_like(arr)
            for idx, (rv, gv, bv) in enumerate([(v,t,p),(q,v,p),(p,v,t),(p,q,v),(t,p,v),(v,p,q)]):
                m = i_idx == idx
                out[:,:,0][m] = rv[m]
                out[:,:,1][m] = gv[m]
                out[:,:,2][m] = bv[m]
            result = Image.fromarray((out * 255).astype(np.uint8), 'RGB')
            _, _, _, a = img.split()
            r2, g2, b2 = result.split()
            img = Image.merge("RGBA", (r2, g2, b2, a))
        if blur > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=blur))
        if vignette > 0:
            width, height = img.size
            arr = np.array(img, dtype=np.float32)
            cx, cy = width / 2, height / 2
            y, x = np.ogrid[:height, :width]
            dist = np.sqrt(((x - cx) / cx) ** 2 + ((y - cy) / cy) ** 2)
            vig = 1 - np.clip(dist * vignette, 0, 1)
            arr[:,:,0] *= vig
            arr[:,:,1] *= vig
            arr[:,:,2] *= vig
            img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        self.current = img
        return self.current
    
    def adjust_temperature(self, value):
      self.current = self.base.copy()
      r, g, b, a = self.current.split()
      if value > 0:
          r = r.point(lambda i: min(255, i + int(value * 30)))
          b = b.point(lambda i: max(0, i - int(value * 30)))
      else:
          r = r.point(lambda i: max(0, i + int(value * 30)))
          b = b.point(lambda i: min(255, i - int(value * 30)))
      self.current = Image.merge("RGBA", (r, g, b, a))
      return self.current

    def adjust_exposure(self, value):
        self.current = self.base.copy()
        self.current = self.current.point(lambda i: max(0, min(255, i * (2 ** value))))
        return self.current

    def adjust_highlights(self, value):
        self.current = self.base.copy()
        self.current = self.current.point(
            lambda i: max(0, min(255, i + int(value * (i / 255))))
        )
        return self.current

    def adjust_shadows(self, value):
        self.current = self.base.copy()
        self.current = self.current.point(
            lambda i: max(0, min(255, i + int(value * (1 - i / 255))))
        )
        return self.current

    def adjust_vibrance(self, value):
        self.current = self.base.copy()
        img = self.current.convert("RGB")
        r, g, b = img.split()
        r_arr = np.array(r, dtype=np.float32)
        g_arr = np.array(g, dtype=np.float32)
        b_arr = np.array(b, dtype=np.float32)
        max_rgb = np.maximum(np.maximum(r_arr, g_arr), b_arr)
        min_rgb = np.minimum(np.minimum(r_arr, g_arr), b_arr)
        saturation = (max_rgb - min_rgb) / (max_rgb + 1e-6)
        factor = 1 + value * (1 - saturation)
        avg = (r_arr + g_arr + b_arr) / 3
        r_arr = np.clip(avg + factor * (r_arr - avg), 0, 255).astype(np.uint8)
        g_arr = np.clip(avg + factor * (g_arr - avg), 0, 255).astype(np.uint8)
        b_arr = np.clip(avg + factor * (b_arr - avg), 0, 255).astype(np.uint8)
        result = Image.merge("RGB", (Image.fromarray(r_arr), Image.fromarray(g_arr), Image.fromarray(b_arr)))
        r2, g2, b2 = result.split()
        _, _, _, a = self.current.split()
        self.current = Image.merge("RGBA", (r2, g2, b2, a))
        return self.current

    def adjust_hue(self, value):
        self.current = self.base.copy()
        img = self.current.convert("RGB")
        arr = np.array(img, dtype=np.float32) / 255.0
        from colorsys import rgb_to_hsv, hsv_to_rgb
        result = np.zeros_like(arr)
        for i in range(arr.shape[0]):
            for j in range(arr.shape[1]):
                h, s, v = rgb_to_hsv(arr[i,j,0], arr[i,j,1], arr[i,j,2])
                h = (h + value / 360.0) % 1.0
                result[i,j] = hsv_to_rgb(h, s, v)
        result = (result * 255).astype(np.uint8)
        rgb = Image.fromarray(result)
        _, _, _, a = self.current.split()
        r, g, b = rgb.split()
        self.current = Image.merge("RGBA", (r, g, b, a))
        return self.current

    def adjust_blur(self, value):
        self.current = self.base.copy()
        if value > 0:
            self.current = self.current.filter(ImageFilter.GaussianBlur(radius=value))
        return self.current

    def adjust_vignette(self, value):
        self.current = self.base.copy()
        if value == 0:
            return self.current
        width, height = self.current.size
        arr = np.array(self.current, dtype=np.float32)
        cx, cy = width / 2, height / 2
        y, x = np.ogrid[:height, :width]
        dist = np.sqrt(((x - cx) / cx) ** 2 + ((y - cy) / cy) ** 2)
        vignette = 1 - np.clip(dist * value, 0, 1)
        arr[:, :, 0] *= vignette
        arr[:, :, 1] *= vignette
        arr[:, :, 2] *= vignette
        self.current = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        return self.current
    
    def apply_adjustments_preview(self, brightness, contrast, saturation, sharpness,
                                 temperature=0, exposure=0, highlights=0, shadows=0,
                                 vibrance=0, hue=0, blur=0, vignette=0):
        preview = self.base.copy()
        if preview.width > 800 or preview.height > 800:
            preview.thumbnail((800, 800), Image.LANCZOS)
        preview = ImageEnhance.Brightness(preview).enhance(brightness)
        preview = ImageEnhance.Contrast(preview).enhance(contrast)
        preview = ImageEnhance.Color(preview).enhance(saturation)
        preview = ImageEnhance.Sharpness(preview).enhance(sharpness)
        return preview
    
   