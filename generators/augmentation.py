"""
图像变异引擎 — 对标准证件图片应用各种图像变换，模拟真实拍摄场景
支持的变异类型：旋转、模糊、光照、噪点、遮挡、透视变换、压缩、翻转、裁剪
"""

import io
import math
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
import cv2


class AugmentationEngine:
    """图像变异引擎"""

    def __init__(self, rng: np.random.RandomState = None):
        self.rng = rng or np.random.RandomState()

    # ── 旋转 ─────────────────────────────────────────
    def rotate(self, img: Image.Image, angle: float, expand: bool = True,
               fillcolor: tuple = (238, 241, 246)) -> Image.Image:
        """
        旋转图片
        angle: 旋转角度（正=逆时针）
        """
        return img.rotate(angle, expand=expand, fillcolor=fillcolor,
                          resample=Image.BICUBIC)

    def rotate_small(self, img: Image.Image) -> Image.Image:
        """模拟拍摄时的轻微倾斜 (-8° ~ +8°)"""
        angle = self.rng.uniform(-8, 8)
        return self.rotate(img, angle), {"type": "rotate", "angle": round(angle, 1)}

    def rotate_medium(self, img: Image.Image) -> Image.Image:
        """模拟中度倾斜 (-25° ~ +25°)"""
        angle = self.rng.uniform(-25, 25)
        return self.rotate(img, angle), {"type": "rotate", "angle": round(angle, 1)}

    def rotate_large(self, img: Image.Image) -> Image.Image:
        """模拟严重倾斜 (-45° ~ +45°)"""
        angle = self.rng.choice([-1, 1]) * self.rng.uniform(30, 45)
        return self.rotate(img, angle), {"type": "rotate", "angle": round(angle, 1)}

    # ── 模糊 ─────────────────────────────────────────
    def blur_gaussian(self, img: Image.Image, radius: float) -> Image.Image:
        """高斯模糊"""
        return img.filter(ImageFilter.GaussianBlur(radius=radius))

    def blur_light(self, img: Image.Image) -> Image.Image:
        """轻微模糊 (模拟轻微手抖)"""
        radius = self.rng.uniform(0.8, 1.5)
        return self.blur_gaussian(img, radius), {"type": "blur", "method": "gaussian", "radius": round(radius, 1)}

    def blur_medium(self, img: Image.Image) -> Image.Image:
        """中度模糊"""
        radius = self.rng.uniform(2.0, 4.0)
        return self.blur_gaussian(img, radius), {"type": "blur", "method": "gaussian", "radius": round(radius, 1)}

    def blur_heavy(self, img: Image.Image) -> Image.Image:
        """严重模糊 (模拟严重手抖/对焦失败)"""
        radius = self.rng.uniform(5.0, 10.0)
        return self.blur_gaussian(img, radius), {"type": "blur", "method": "gaussian", "radius": round(radius, 1)}

    def blur_motion(self, img: Image.Image) -> Image.Image:
        """运动模糊"""
        # 用 OpenCV 实现
        arr = np.array(img)
        size = self.rng.randint(10, 25)
        angle = self.rng.uniform(0, 360)
        # 创建运动模糊核
        kernel = np.zeros((size, size))
        center = size // 2
        rad = math.radians(angle)
        for i in range(size):
            x = int(center + (i - center) * math.cos(rad))
            y = int(center + (i - center) * math.sin(rad))
            if 0 <= x < size and 0 <= y < size:
                kernel[y, x] = 1
        kernel /= kernel.sum()
        blurred = cv2.filter2D(arr, -1, kernel)
        return Image.fromarray(blurred), {"type": "blur", "method": "motion", "size": size}

    # ── 光照 ─────────────────────────────────────────
    def brightness(self, img: Image.Image, factor: float) -> Image.Image:
        """调整亮度 factor: >1 变亮, <1 变暗"""
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(factor)

    def contrast(self, img: Image.Image, factor: float) -> Image.Image:
        """调整对比度"""
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)

    def lighting_dark(self, img: Image.Image) -> Image.Image:
        """暗光环境"""
        factor = self.rng.uniform(0.3, 0.6)
        return self.brightness(img, factor), {"type": "lighting", "method": "dark", "factor": round(factor, 2)}

    def lighting_bright(self, img: Image.Image) -> Image.Image:
        """过曝"""
        factor = self.rng.uniform(1.5, 2.2)
        img_bright = self.brightness(img, factor)
        img_low_contrast = self.contrast(img_bright, 0.6)
        return img_low_contrast, {"type": "lighting", "method": "overexposed", "factor": round(factor, 2)}

    def lighting_uneven(self, img: Image.Image) -> Image.Image:
        """不均匀光照 (一侧亮一侧暗)"""
        arr = np.array(img, dtype=np.float32)
        h, w = arr.shape[:2]

        # 生成渐变遮罩
        gradient = np.linspace(0.4, 1.4, w).reshape(1, w, 1)
        gradient = np.tile(gradient, (h, 1, 1))

        arr = np.clip(arr * gradient, 0, 255).astype(np.uint8)
        return Image.fromarray(arr), {"type": "lighting", "method": "uneven"}

    def lighting_spotlight(self, img: Image.Image) -> Image.Image:
        """闪光灯反光 (中间亮斑)"""
        arr = np.array(img, dtype=np.float32)
        h, w = arr.shape[:2]
        cx, cy = self.rng.randint(w//4, 3*w//4), self.rng.randint(h//4, 3*h//4)
        radius = self.rng.randint(100, 300)

        y, x = np.ogrid[:h, :w]
        dist = np.sqrt((x - cx)**2 + (y - cy)**2)
        mask = np.clip(1.0 + 0.8 * np.exp(-dist**2 / (2 * radius**2)), 1.0, 1.8)
        mask = mask[:, :, np.newaxis]

        arr = np.clip(arr * mask, 0, 255).astype(np.uint8)
        return Image.fromarray(arr), {"type": "lighting", "method": "spotlight"}

    # ── 噪点 ─────────────────────────────────────────
    def noise_gaussian(self, img: Image.Image, sigma: float) -> Image.Image:
        """高斯噪声"""
        arr = np.array(img, dtype=np.float32)
        noise = self.rng.normal(0, sigma, arr.shape)
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)

    def noise_light(self, img: Image.Image) -> Image.Image:
        return self.noise_gaussian(img, 5), {"type": "noise", "method": "gaussian", "sigma": 5}

    def noise_medium(self, img: Image.Image) -> Image.Image:
        return self.noise_gaussian(img, 15), {"type": "noise", "method": "gaussian", "sigma": 15}

    def noise_heavy(self, img: Image.Image) -> Image.Image:
        return self.noise_gaussian(img, 30), {"type": "noise", "method": "gaussian", "sigma": 30}

    def noise_salt_pepper(self, img: Image.Image, prob: float = 0.02) -> Image.Image:
        """椒盐噪声"""
        arr = np.array(img).copy()
        h, w = arr.shape[:2]
        mask = self.rng.random((h, w)) < prob
        arr[mask] = self.rng.choice([0, 255], size=mask.sum()).reshape(-1, 1)
        return Image.fromarray(arr)

    # ── 遮挡 ─────────────────────────────────────────
    def occlude_random(self, img: Image.Image, num_blocks: int = None) -> Image.Image:
        """随机矩形遮挡"""
        if num_blocks is None:
            num_blocks = self.rng.randint(1, 5)
        arr = np.array(img).copy()
        h, w = arr.shape[:2]
        for _ in range(num_blocks):
            bw = self.rng.randint(20, w // 5)
            bh = self.rng.randint(20, h // 5)
            bx = self.rng.randint(0, w - bw)
            by = self.rng.randint(0, h - bh)
            color = self.rng.randint(0, 200, 3)
            arr[by:by+bh, bx:bx+bw] = color
        return Image.fromarray(arr), {"type": "occlusion", "method": "blocks", "count": num_blocks}

    def occlude_finger(self, img: Image.Image) -> Image.Image:
        """模拟手指遮挡 (圆形+椭圆区域)"""
        arr = np.array(img).copy()
        h, w = arr.shape[:2]
        # 生成 1-3 个椭圆形遮挡
        for _ in range(self.rng.randint(1, 3)):
            cx = self.rng.randint(w//4, 3*w//4)
            cy = self.rng.randint(h//4, 3*h//4)
            rx = self.rng.randint(20, 80)
            ry = self.rng.randint(30, 120)
            angle = self.rng.uniform(0, 180)
            color = self.rng.randint(180, 240, 3)
            # 在椭圆形内填充
            y, x = np.ogrid[:h, :w]
            cos_a = math.cos(math.radians(angle))
            sin_a = math.sin(math.radians(angle))
            x_rot = (x - cx) * cos_a + (y - cy) * sin_a
            y_rot = -(x - cx) * sin_a + (y - cy) * cos_a
            mask = (x_rot / rx) ** 2 + (y_rot / ry) ** 2 <= 1
            arr[mask] = color
        return Image.fromarray(arr), {"type": "occlusion", "method": "finger"}

    # ── 透视变换 ─────────────────────────────────────
    def perspective(self, img: Image.Image, intensity: float = 0.15) -> Image.Image:
        """模拟非正对拍摄的透视变换"""
        w, h = img.size
        src_pts = np.float32([[0, 0], [w, 0], [w, h], [0, h]])

        offset = int(w * intensity)
        dx1 = self.rng.randint(-offset, offset)
        dy1 = self.rng.randint(-offset // 2, offset // 2)
        dx2 = w + self.rng.randint(-offset, offset)
        dy2 = self.rng.randint(-offset // 2, offset // 2)
        dx3 = w + self.rng.randint(-offset, offset)
        dy3 = h + self.rng.randint(-offset // 2, offset // 2)
        dx4 = self.rng.randint(-offset, offset)
        dy4 = h + self.rng.randint(-offset // 2, offset // 2)

        dst_pts = np.float32([[dx1, dy1], [dx2, dy2], [dx3, dy3], [dx4, dy4]])

        matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
        arr = np.array(img)
        result = cv2.warpPerspective(
            arr, matrix, (w, h),
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(238, 241, 246)
        )
        return Image.fromarray(result), {"type": "perspective", "intensity": intensity}

    # ── JPEG 压缩 ────────────────────────────────────
    def jpeg_compress(self, img: Image.Image, quality: int) -> Image.Image:
        """JPEG 压缩 (模拟微信/传输压缩)"""
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        buf.seek(0)
        return Image.open(buf)

    def compress_light(self, img: Image.Image) -> Image.Image:
        quality = self.rng.randint(60, 80)
        return self.jpeg_compress(img, quality), {"type": "compress", "method": "jpeg", "quality": quality}

    def compress_heavy(self, img: Image.Image) -> Image.Image:
        quality = self.rng.randint(20, 45)
        return self.jpeg_compress(img, quality), {"type": "compress", "method": "jpeg", "quality": quality}

    # ── 翻转/镜像 ────────────────────────────────────
    def flip_horizontal(self, img: Image.Image) -> Image.Image:
        return img.transpose(Image.FLIP_LEFT_RIGHT), {"type": "flip", "method": "horizontal"}

    def flip_vertical(self, img: Image.Image) -> Image.Image:
        return img.transpose(Image.FLIP_TOP_BOTTOM), {"type": "flip", "method": "vertical"}

    def rotate_180(self, img: Image.Image) -> Image.Image:
        return img.rotate(180), {"type": "rotate", "angle": 180}

    # ── 裁剪/不全 ────────────────────────────────────
    def crop_partial(self, img: Image.Image, ratio: float = None) -> Image.Image:
        """裁剪掉一部分 (模拟证件不全)"""
        if ratio is None:
            ratio = self.rng.uniform(0.05, 0.25)
        w, h = img.size
        side = self.rng.choice(["left", "right", "top", "bottom"])
        if side == "left":
            crop_w = int(w * ratio)
            return img.crop((crop_w, 0, w, h)), {"type": "crop", "side": side, "ratio": round(ratio, 2)}
        elif side == "right":
            crop_w = int(w * (1 - ratio))
            return img.crop((0, 0, crop_w, h)), {"type": "crop", "side": side, "ratio": round(ratio, 2)}
        elif side == "top":
            crop_h = int(h * ratio)
            return img.crop((0, crop_h, w, h)), {"type": "crop", "side": side, "ratio": round(ratio, 2)}
        else:
            crop_h = int(h * (1 - ratio))
            return img.crop((0, 0, w, crop_h)), {"type": "crop", "side": side, "ratio": round(ratio, 2)}

    # ── 缩放/分辨率 ──────────────────────────────────
    def downscale(self, img: Image.Image, scale: float) -> Image.Image:
        """降低分辨率"""
        w, h = img.size
        new_w, new_h = int(w * scale), int(h * scale)
        return img.resize((new_w, new_h), Image.LANCZOS).resize((w, h), Image.LANCZOS)

    def downscale_medium(self, img: Image.Image) -> Image.Image:
        scale = self.rng.uniform(0.4, 0.7)
        return self.downscale(img, scale), {"type": "downscale", "scale": round(scale, 2)}

    def downscale_low(self, img: Image.Image) -> Image.Image:
        scale = self.rng.uniform(0.15, 0.35)
        return self.downscale(img, scale), {"type": "downscale", "scale": round(scale, 2)}

    # ── 复合变异 ─────────────────────────────────────
    def apply_all_variants(self, img: Image.Image) -> list:
        """
        对一个标准图片应用所有变异类型，返回 [(变体图片, 变异描述), ...]
        """
        variants = []

        # 旋转系列
        for name, method in [
            ("rotate_small", self.rotate_small),
            ("rotate_medium", self.rotate_medium),
            ("rotate_large", self.rotate_large),
        ]:
            result, meta = method(img)
            variants.append((result, meta))

        # 模糊系列
        for name, method in [
            ("blur_light", self.blur_light),
            ("blur_medium", self.blur_medium),
            ("blur_heavy", self.blur_heavy),
            ("blur_motion", self.blur_motion),
        ]:
            result, meta = method(img)
            variants.append((result, meta))

        # 光照系列
        for name, method in [
            ("lighting_dark", self.lighting_dark),
            ("lighting_bright", self.lighting_bright),
            ("lighting_uneven", self.lighting_uneven),
            ("lighting_spotlight", self.lighting_spotlight),
        ]:
            result, meta = method(img)
            variants.append((result, meta))

        # 噪点系列
        for name, method in [
            ("noise_light", self.noise_light),
            ("noise_medium", self.noise_medium),
            ("noise_heavy", self.noise_heavy),
        ]:
            result, meta = method(img)
            variants.append((result, meta))

        # 遮挡
        for name, method in [
            ("occlude_random", self.occlude_random),
            ("occlude_finger", self.occlude_finger),
        ]:
            result, meta = method(img)
            variants.append((result, meta))

        # 透视
        result, meta = self.perspective(img, 0.12)
        variants.append((result, meta))

        # 压缩
        for name, method in [
            ("compress_light", self.compress_light),
            ("compress_heavy", self.compress_heavy),
        ]:
            result, meta = method(img)
            variants.append((result, meta))

        # 翻转
        result, meta = self.flip_horizontal(img)
        variants.append((result, meta))
        result, meta = self.rotate_180(img)
        variants.append((result, meta))

        # 裁剪
        result, meta = self.crop_partial(img, 0.15)
        variants.append((result, meta))

        # 低分辨率
        for name, method in [
            ("downscale_medium", self.downscale_medium),
            ("downscale_low", self.downscale_low),
        ]:
            result, meta = method(img)
            variants.append((result, meta))

        return variants

    def apply_selected_variants(self, img: Image.Image, variant_names: list) -> list:
        """仅应用指定的变异类型"""
        variant_map = {
            "rotate_small": self.rotate_small,
            "rotate_medium": self.rotate_medium,
            "rotate_large": self.rotate_large,
            "blur_light": self.blur_light,
            "blur_medium": self.blur_medium,
            "blur_heavy": self.blur_heavy,
            "blur_motion": self.blur_motion,
            "lighting_dark": self.lighting_dark,
            "lighting_bright": self.lighting_bright,
            "lighting_uneven": self.lighting_uneven,
            "lighting_spotlight": self.lighting_spotlight,
            "noise_light": self.noise_light,
            "noise_medium": self.noise_medium,
            "noise_heavy": self.noise_heavy,
            "occlude_random": self.occlude_random,
            "occlude_finger": self.occlude_finger,
            "perspective": lambda img: self.perspective(img, 0.12),
            "compress_light": self.compress_light,
            "compress_heavy": self.compress_heavy,
            "flip_horizontal": self.flip_horizontal,
            "rotate_180": self.rotate_180,
            "crop_partial": lambda img: self.crop_partial(img, 0.15),
            "downscale_medium": self.downscale_medium,
            "downscale_low": self.downscale_low,
        }

        variants = []
        for name in variant_names:
            if name in variant_map:
                result, meta = variant_map[name](img)
                variants.append((result, meta))
        return variants
