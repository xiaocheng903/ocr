"""
证件图像渲染器 — 将字段值渲染为逼真的证件图片
支持：身份证（人像面/国徽面）、银行卡、学历证书、学位证书、离职证明
"""

import io
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# ── 字体配置 ──────────────────────────────────────────────
_WIN_FONTS_DIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
FONT_CANDIDATES = {
    # 优先保证中文可显示
    "sans": [
        os.path.join(_WIN_FONTS_DIR, "msyh.ttc"),
        os.path.join(_WIN_FONTS_DIR, "simhei.ttf"),
        os.path.join(_WIN_FONTS_DIR, "simsun.ttc"),
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ],
    "serif": [
        os.path.join(_WIN_FONTS_DIR, "simsun.ttc"),
        os.path.join(_WIN_FONTS_DIR, "simhei.ttf"),
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ],
    "mono": [
        os.path.join(_WIN_FONTS_DIR, "consola.ttf"),
        os.path.join(_WIN_FONTS_DIR, "cour.ttf"),
        os.path.join(_WIN_FONTS_DIR, "simsun.ttc"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ],
    "kai": [
        os.path.join(_WIN_FONTS_DIR, "simkai.ttf"),
        os.path.join(_WIN_FONTS_DIR, "simsun.ttc"),
        "/usr/share/fonts/truetype/arphic/ukai.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    ],
}


def _load_font(size: int, style: str = "sans") -> ImageFont.FreeTypeFont:
    candidates = FONT_CANDIDATES.get(style, FONT_CANDIDATES["sans"])
    errors = []
    for font_path in candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except OSError as exc:
            errors.append(f"{font_path}: {exc}")

    # 极限兜底，避免程序直接崩溃（中文可能退化为方块）
    try:
        return ImageFont.load_default()
    except Exception as exc:
        tried = "\n".join(errors)
        raise RuntimeError(
            f"无法加载字体(style={style})。尝试路径:\n{tried}"
        ) from exc


def _draw_text_centered(
    draw: ImageDraw.Draw,
    text: str,
    rect: tuple,
    fill="black",
    font: ImageFont.FreeTypeFont = None,
    font_size: int = 24,
):
    """在指定矩形区域内居中绘制文字"""
    if font is None:
        font = _load_font(font_size)
    x1, y1, x2, y2 = rect
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = x1 + (x2 - x1 - tw) / 2
    y = y1 + (y2 - y1 - th) / 2
    draw.text((x, y), text, fill=fill, font=font)


class IDCardRenderer:
    """身份证渲染器 — 生成身份证正反面图片"""

    CARD_W = 1020  # 实际比例 85.6mm : 54mm ≈ 1020 : 643
    CARD_H = 643
    CANVAS_PAD = 80  # 画布留白
    CANVAS_W = CARD_W + CANVAS_PAD * 2
    CANVAS_H = CARD_H + CANVAS_PAD * 2

    def __init__(self, rng: np.random.RandomState = None):
        self.rng = rng or np.random.RandomState()

    def _card_rect(self) -> tuple:
        """卡面在画布中的矩形区域"""
        return (self.CANVAS_PAD, self.CANVAS_PAD,
                self.CANVAS_PAD + self.CARD_W, self.CANVAS_PAD + self.CARD_H)

    def _add_noise(self, img: Image.Image, amount: int = 800):
        """添加模拟拍摄噪点"""
        pixels = img.load()
        w, h = img.size
        for _ in range(amount):
            x = self.rng.randint(self.CANVAS_PAD + 5, self.CANVAS_PAD + self.CARD_W - 5)
            y = self.rng.randint(self.CANVAS_PAD + 5, self.CANVAS_PAD + self.CARD_H - 5)
            r, g, b = pixels[x, y]
            c = self.rng.randint(-15, 15)
            pixels[x, y] = (
                max(0, min(255, r + c)),
                max(0, min(255, g + c)),
                max(0, min(255, b + c)),
            )

    def _add_fine_lines(self, draw: ImageDraw.Draw):
        """添加细密防伪纹理线"""
        for x in range(self.CANVAS_PAD + 20, self.CANVAS_PAD + self.CARD_W - 20, 7):
            for y in range(self.CANVAS_PAD + 20, self.CANVAS_PAD + self.CARD_H - 20):
                if (x * 13 + y * 7) % 173 == 0:
                    draw.point((x, y), fill=(230, 230, 230))

    def render_front(self, profile: dict) -> Image.Image:
        """渲染身份证人像面"""
        img = Image.new("RGB", (self.CANVAS_W, self.CANVAS_H), (238, 241, 246))
        draw = ImageDraw.Draw(img)

        cx1, cy1, cx2, cy2 = self._card_rect()

        # 卡面底色 + 阴影
        draw.rectangle([cx1 + 8, cy1 + 10, cx2 + 8, cy2 + 10], fill=(206, 211, 220))
        draw.rectangle([cx1, cy1, cx2, cy2], fill=(252, 252, 251))
        draw.rectangle([cx1, cy1, cx2, cy2], outline=(164, 170, 182), width=2)

        # 顶部渐变标题区
        for y in range(cy1 + 15, cy1 + 100):
            t = (y - cy1 - 15) / 85
            r = int(246 * (1 - t) + 240 * t)
            g = int(227 * (1 - t) + 218 * t)
            b = int(214 * (1 - t) + 202 * t)
            draw.line([(cx1 + 15, y), (cx2 - 15, y)], fill=(r, g, b))

        # 标题文字
        font_title = _load_font(32, "sans")
        font_field = _load_font(28, "sans")
        font_value = _load_font(28, "kai")

        draw.text((cx1 + 30, cy1 + 38), "中华人民共和国", fill=(80, 40, 20), font=font_title)
        draw.text((cx1 + 30, cy1 + 72), "居民身份证", fill=(80, 40, 20), font=font_title)

        # 头像区域
        photo_x1, photo_y1 = cx1 + self.CARD_W - 300, cy1 + 145
        photo_x2, photo_y2 = photo_x1 + 220, photo_y1 + 280
        draw.rectangle([photo_x1, photo_y1, photo_x2, photo_y2],
                       fill=(210, 215, 225), outline=(150, 155, 165), width=2)

        # 绘制模拟头像
        face_cx = photo_x1 + 110
        face_cy = photo_y1 + 100
        draw.ellipse([face_cx - 50, face_cy - 60, face_cx + 50, face_cy + 20],
                     fill=(220, 200, 180))
        draw.ellipse([face_cx - 35, face_cy + 25, face_cx + 35, face_cy + 90],
                     fill=(210, 190, 170))

        # 字段（按标签宽度和像素宽度动态排版，避免任何遮挡）
        fields_data = [
            ("姓名", profile["name"]),
            ("性别", profile["gender"]),
            ("民族", profile["ethnicity"]),
            ("出生", profile["birth_date"]),
            ("住址", profile["address"]),
            ("公民身份号码", profile["id_number"]),
        ]

        def wrap_text_by_width(text, font, max_width):
            lines = []
            current = ""
            for ch in text:
                candidate = current + ch
                bbox = draw.textbbox((0, 0), candidate, font=font)
                width = bbox[2] - bbox[0]
                if current and width > max_width:
                    lines.append(current)
                    current = ch
                else:
                    current = candidate
            if current:
                lines.append(current)
            return lines or [""]

        label_x = cx1 + 28
        base_value_x = cx1 + 210
        y_cursor = cy1 + 148
        row_step = 52
        wrapped_line_step = 34
        value_right_limit = photo_x1 - 24

        for label, value in fields_data:
            draw.text((label_x, y_cursor), label, fill=(60, 60, 60), font=font_field)

            label_bbox = draw.textbbox((0, 0), label, font=font_field)
            label_width = label_bbox[2] - label_bbox[0]
            value_x = max(base_value_x, label_x + label_width + 20)
            value_max_width = max(120, value_right_limit - value_x)

            if label == "住址":
                lines = wrap_text_by_width(value, font_value, value_max_width)
                for idx, line in enumerate(lines):
                    draw.text((value_x, y_cursor + idx * wrapped_line_step), line, fill=(20, 20, 20), font=font_value)
                y_cursor += row_step + (len(lines) - 1) * wrapped_line_step
            elif label == "公民身份号码":
                font_id = _load_font(30, "mono")
                draw.text((value_x, y_cursor), value, fill=(20, 20, 20), font=font_id)
                y_cursor += row_step
            else:
                draw.text((value_x, y_cursor), value, fill=(20, 20, 20), font=font_value)
                y_cursor += row_step

        # 防伪纹理
        self._add_fine_lines(draw)
        self._add_noise(img, amount=600)

        # "测试样张" 水印（放在更靠下位置，避免压住正文）
        font_watermark = _load_font(22, "sans")
        wm_x = cx1 + self.CARD_W // 2 - 70
        wm_y = cy1 + self.CARD_H - 55
        draw.text((wm_x, wm_y), "【测试样张】",
                  fill=(200, 50, 50, 80), font=font_watermark)

        return img

    def render_back(self, profile: dict) -> Image.Image:
        """渲染身份证国徽面"""
        img = Image.new("RGB", (self.CANVAS_W, self.CANVAS_H), (238, 241, 246))
        draw = ImageDraw.Draw(img)

        cx1, cy1, cx2, cy2 = self._card_rect()

        # 卡面底色
        draw.rectangle([cx1 + 8, cy1 + 10, cx2 + 8, cy2 + 10], fill=(206, 211, 220))
        draw.rectangle([cx1, cy1, cx2, cy2], fill=(252, 252, 251))
        draw.rectangle([cx1, cy1, cx2, cy2], outline=(164, 170, 182), width=2)

        # 顶部渐变
        for y in range(cy1 + 15, cy1 + 100):
            t = (y - cy1 - 15) / 85
            r = int(219 * (1 - t) + 212 * t)
            g = int(230 * (1 - t) + 223 * t)
            b = int(248 * (1 - t) + 242 * t)
            draw.line([(cx1 + 15, y), (cx2 - 15, y)], fill=(r, g, b))

        # 标题
        font_title = _load_font(30, "sans")
        draw.text((cx1 + 30, cy1 + 38), "中华人民共和国", fill=(80, 40, 20), font=font_title)
        draw.text((cx1 + 30, cy1 + 72), "居民身份证", fill=(80, 40, 20), font=font_title)

        # 国徽（简化绘制）
        gb_cx, gb_cy = cx1 + self.CARD_W // 2, cy1 + 280
        # 外圈
        draw.ellipse([gb_cx - 90, gb_cy - 90, gb_cx + 90, gb_cy + 90],
                     outline=(180, 120, 50), width=3)
        draw.ellipse([gb_cx - 75, gb_cy - 75, gb_cx + 75, gb_cy + 75],
                     outline=(180, 120, 50), width=2)
        # 五星
        for angle in range(0, 360, 72):
            import math
            rad = math.radians(angle)
            sx = gb_cx + int(50 * math.cos(rad))
            sy = gb_cy + int(50 * math.sin(rad))
            draw.ellipse([sx - 8, sy - 8, sx + 8, sy + 8],
                         fill=(180, 120, 50))
        # 天安门简化
        draw.rectangle([gb_cx - 50, gb_cy - 10, gb_cx + 50, gb_cy + 40],
                       fill=(200, 160, 80))

        # 签发机关 & 有效期限
        font_field = _load_font(24, "sans")
        font_value = _load_font(26, "kai")

        # 签发机关
        draw.text((cx1 + 28, cy1 + 420), "签发机关", fill=(60, 60, 60), font=font_field)
        area_code = profile["id_number"][:6]
        draw.text((cx1 + 160, cy1 + 420), f"{area_code}公安局", fill=(20, 20, 20), font=font_value)

        # 有效期限
        draw.text((cx1 + 28, cy1 + 470), "有效期限", fill=(60, 60, 60), font=font_field)
        birth = profile["birth_date"]
        # 有效期：签发日 ~ 签发日+20年
        year = int(birth[:4]) + self.rng.randint(20, 40)
        draw.text((cx1 + 160, cy1 + 470),
                  f"{year - 5}.01.01-{year + 15}.01.01",
                  fill=(20, 20, 20), font=font_value)

        self._add_fine_lines(draw)
        self._add_noise(img, amount=500)

        font_watermark = _load_font(22, "sans")
        draw.text((cx1 + 350, cy1 + 520), "【测试样张】",
                  fill=(200, 50, 50, 80), font=font_watermark)

        return img


class BankCardRenderer:
    """银行卡渲染器"""

    CARD_W = 960
    CARD_H = 610
    CANVAS_PAD = 80
    CANVAS_W = CARD_W + CANVAS_PAD * 2
    CANVAS_H = CARD_H + CANVAS_PAD * 2

    # 银行主题色
    BANK_COLORS = {
        "中国工商银行": ((200, 50, 50), (180, 30, 30)),
        "中国农业银行": ((0, 100, 70), (0, 70, 50)),
        "中国银行": ((180, 30, 30), (140, 20, 20)),
        "中国建设银行": ((0, 80, 160), (0, 60, 130)),
        "招商银行": ((200, 50, 40), (160, 30, 25)),
        "交通银行": ((0, 80, 160), (0, 60, 130)),
        "浦发银行": ((0, 90, 160), (0, 70, 130)),
        "兴业银行": ((0, 100, 80), (0, 75, 60)),
        "中信银行": ((180, 50, 40), (150, 30, 20)),
        "民生银行": ((0, 120, 80), (0, 90, 60)),
        "光大银行": ((120, 0, 120), (90, 0, 90)),
        "平安银行": ((220, 120, 30), (190, 100, 20)),
    }

    def __init__(self, rng: np.random.RandomState = None):
        self.rng = rng or np.random.RandomState()

    def render(self, profile: dict) -> Image.Image:
        img = Image.new("RGB", (self.CANVAS_W, self.CANVAS_H), (245, 248, 252))
        draw = ImageDraw.Draw(img)

        cx1, cy1 = self.CANVAS_PAD, self.CANVAS_PAD
        cx2, cy2 = cx1 + self.CARD_W, cy1 + self.CARD_H

        # 阴影
        draw.rectangle([cx1 + 8, cy1 + 10, cx2 + 8, cy2 + 10], fill=(180, 185, 195))

        # 顶部色带
        top_color, _ = self.BANK_COLORS.get(profile["bank_name"], ((50, 50, 150), (30, 30, 130)))
        draw.rectangle([cx1, cy1, cx2, cy1 + 110], fill=top_color)

        # 银行名
        font_bank = _load_font(38, "sans")
        draw.text((cx1 + 40, cy1 + 30), profile["bank_name"],
                  fill="white", font=font_bank)

        # 银联标识
        font_union = _load_font(18, "sans")
        draw.text((cx2 - 140, cy1 + 55), "UnionPay", fill="white", font=font_union)
        draw.text((cx2 - 140, cy1 + 75), "银  联", fill="white", font=font_union)

        # 芯片
        chip_x1, chip_y1 = cx1 + 60, cy1 + 170
        draw.rounded_rectangle(
            [chip_x1, chip_y1, chip_x1 + 70, chip_y1 + 55],
            radius=8, fill=(220, 200, 140), outline=(180, 155, 90), width=2
        )

        # 卡号
        font_card_no = _load_font(32, "mono")
        card_no = profile["bank_card"]
        formatted = " ".join([card_no[i:i+4] for i in range(0, len(card_no), 4)])
        draw.text((cx1 + 40, cy1 + 260), formatted, fill=(30, 30, 30), font=font_card_no)

        # 有效期 / 持卡人
        font_small = _load_font(18, "sans")
        font_value = _load_font(22, "kai")
        draw.text((cx1 + 40, cy1 + 340), "VALID THRU", fill=(100, 100, 100), font=font_small)
        draw.text((cx1 + 40, cy1 + 365), "12/30", fill=(30, 30, 30), font=font_value)

        # 持卡人
        draw.text((cx1 + 40, cy1 + 430), "CARDHOLDER", fill=(100, 100, 100), font=font_small)
        # 拼音
        import unicodedata
        draw.text((cx1 + 40, cy1 + 455), profile["name"].upper(),
                  fill=(30, 30, 30), font=_load_font(24, "sans"))

        # 底部色带
        draw.rectangle([cx1, cy2 - 5, cx2, cy2], fill=top_color)

        # 水印
        font_wm = _load_font(18, "sans")
        draw.text((cx1 + 600, cy1 + 500), "【测试样张】",
                  fill=(200, 50, 50, 60), font=font_wm)

        # 噪点
        for _ in range(500):
            x = self.rng.randint(cx1 + 10, cx2 - 10)
            y = self.rng.randint(cy1 + 130, cy2 - 20)
            px = img.getpixel((x, y))
            c = self.rng.randint(-10, 10)
            img.putpixel((x, y), (
                max(0, min(255, px[0] + c)),
                max(0, min(255, px[1] + c)),
                max(0, min(255, px[2] + c)),
            ))

        return img


class CertificateRenderer:
    """证书类文档渲染器 — 学历证书、学位证书、离职证明等"""

    CANVAS_W = 1240  # 适中分辨率
    CANVAS_H = 1754
    MARGIN = 120

    def __init__(self, rng: np.random.RandomState = None):
        self.rng = rng or np.random.RandomState()

    def _create_base(self) -> tuple:
        img = Image.new("RGB", (self.CANVAS_W, self.CANVAS_H), (253, 252, 248))
        draw = ImageDraw.Draw(img)
        # 边框
        m = self.MARGIN
        draw.rectangle([m, m, self.CANVAS_W - m, self.CANVAS_H - m],
                       outline=(120, 100, 60), width=6)
        draw.rectangle([m + 20, m + 20, self.CANVAS_W - m - 20, self.CANVAS_H - m - 20],
                       outline=(160, 140, 90), width=3)
        return img, draw

    def render_education(self, profile: dict) -> Image.Image:
        """渲染学历证书"""
        img, draw = self._create_base()
        edu = profile["education"]

        # 校徽位置
        cx = self.CANVAS_W // 2
        draw.ellipse([cx - 60, self.MARGIN + 80, cx + 60, self.MARGIN + 200],
                     outline=(120, 60, 20), width=3)

        # 标题
        font_title = _load_font(36, "kai")
        _draw_text_centered(draw, edu["university"], 
                           (self.MARGIN, self.MARGIN + 140, self.CANVAS_W - self.MARGIN, self.MARGIN + 190),
                           fill=(80, 30, 20), font=font_title)

        font_subtitle = _load_font(28, "kai")
        _draw_text_centered(draw, "学历证书",
                           (self.MARGIN, self.MARGIN + 195, self.CANVAS_W - self.MARGIN, self.MARGIN + 235),
                           fill=(80, 30, 20), font=font_subtitle)

        # 正文
        font_body = _load_font(22, "kai")
        body_lines = [
            f"学生 {profile['name']}，{profile['gender']}，",
            f"{profile['birth_date']} 生，",
            f"于 {edu['start_date']} 至 {edu['end_date']}",
            f"在本校 {edu['major']} 专业",
            f"{edu['level']} 学习，修完教学计划规定的全部课程，",
            f"成绩合格，准予毕业。",
        ]

        y = self.MARGIN + 280
        for line in body_lines:
            bbox = draw.textbbox((0, 0), line, font=font_body)
            tw = bbox[2] - bbox[0]
            x = (self.CANVAS_W - tw) / 2
            draw.text((x, y), line, fill=(40, 30, 20), font=font_body)
            y += 40

        # 校长签名/日期/证书编号
        y = self.CANVAS_H - self.MARGIN - 180
        font_small = _load_font(18, "kai")
        draw.text((self.MARGIN + 60, y), f"证书编号：{edu.get('cert_no', '')}",
                  fill=(60, 50, 40), font=font_small)
        draw.text((self.CANVAS_W - self.MARGIN - 300, y + 50), "校（院）长：__________",
                  fill=(60, 50, 40), font=font_small)
        draw.text((self.CANVAS_W - self.MARGIN - 300, y + 100), f"{edu['end_date'][:4]}年6月30日",
                  fill=(60, 50, 40), font=font_small)

        # 防伪水印
        font_wm = _load_font(14, "sans")
        draw.text((self.MARGIN + 50, self.CANVAS_H - self.MARGIN - 50),
                  "【测试样张 - OCR测试数据】", fill=(200, 180, 160), font=font_wm)

        # 噪点
        self._add_paper_texture(img)
        return img

    def render_degree(self, profile: dict) -> Image.Image:
        """渲染学位证书"""
        img, draw = self._create_base()
        edu = profile["education"]

        font_title = _load_font(36, "kai")
        _draw_text_centered(draw, "学士学位证书" if "学士" in edu["degree"] else "硕士学位证书",
                           (self.MARGIN, self.MARGIN + 100, self.CANVAS_W - self.MARGIN, self.MARGIN + 150),
                           fill=(80, 30, 20), font=font_title)

        font_body = _load_font(22, "kai")
        body_lines = [
            f"{profile['name']}，{profile['gender']}，",
            f"{profile['birth_date']} 生。",
            f"在 {edu['university']}",
            f"{edu['major']} 专业完成了",
            f"{edu['level']} 学习计划，",
            f"经审核符合《中华人民共和国学位条例》规定，",
            f"授予 {edu['degree']} 学位。",
        ]

        y = self.MARGIN + 260
        for line in body_lines:
            bbox = draw.textbbox((0, 0), line, font=font_body)
            x = (self.CANVAS_W - bbox[2] + bbox[0]) / 2
            draw.text((x, y), line, fill=(40, 30, 20), font=font_body)
            y += 40

        font_small = _load_font(18, "kai")
        y2 = self.CANVAS_H - self.MARGIN - 180
        draw.text((self.MARGIN + 60, y2), f"证书编号：{edu.get('cert_no', '')}",
                  fill=(60, 50, 40), font=font_small)
        draw.text((self.CANVAS_W - self.MARGIN - 300, y2 + 100), f"{edu['end_date'][:4]}年6月30日",
                  fill=(60, 50, 40), font=font_small)

        self._add_paper_texture(img)
        return img

    def render_study_proof(self, profile: dict) -> Image.Image:
        """渲染在读证明"""
        img, draw = self._create_base()
        edu = profile["education"]

        # 头部
        font_school = _load_font(34, "kai")
        _draw_text_centered(
            draw,
            edu.get("university", "某某大学"),
            (self.MARGIN, self.MARGIN + 120, self.CANVAS_W - self.MARGIN, self.MARGIN + 170),
            fill=(80, 30, 20),
            font=font_school,
        )

        font_title = _load_font(30, "kai")
        _draw_text_centered(
            draw,
            "在读证明",
            (self.MARGIN, self.MARGIN + 180, self.CANVAS_W - self.MARGIN, self.MARGIN + 230),
            fill=(80, 30, 20),
            font=font_title,
        )

        # 正文
        font_body = _load_font(22, "kai")
        body_lines = [
            f"兹证明 {profile['name']}，{profile['gender']}，身份证号：{profile['id_number']}，",
            f"系我校 {edu.get('major', '')} 专业 {edu.get('level', '')} 在读学生。",
            f"入学时间：{edu.get('start_date', '')}",
            f"预计毕业时间：{edu.get('end_date', '')}",
            f"学号：{edu.get('cert_no', '')}",
            "特此证明。",
        ]

        y = self.MARGIN + 300
        for line in body_lines:
            draw.text((self.MARGIN + 80, y), line, fill=(40, 30, 20), font=font_body)
            y += 52

        # 落款
        font_small = _load_font(20, "kai")
        draw.text(
            (self.CANVAS_W - self.MARGIN - 360, self.CANVAS_H - self.MARGIN - 180),
            edu.get("university", "某某大学") + " 教务处",
            fill=(60, 50, 40),
            font=font_small,
        )
        draw.text(
            (self.CANVAS_W - self.MARGIN - 360, self.CANVAS_H - self.MARGIN - 130),
            f"{edu.get('end_date', '2026-06-30')[:4]}年01月01日",
            fill=(60, 50, 40),
            font=font_small,
        )

        # 公章
        seal_cx = self.CANVAS_W - self.MARGIN - 180
        seal_cy = self.CANVAS_H - self.MARGIN - 110
        draw.ellipse([seal_cx - 70, seal_cy - 70, seal_cx + 70, seal_cy + 70],
                     outline=(200, 50, 50), width=4)
        font_seal = _load_font(16, "sans")
        _draw_text_centered(draw, "教务处", (seal_cx - 55, seal_cy - 30, seal_cx + 55, seal_cy + 30),
                           fill=(200, 50, 50), font=font_seal)

        # 防伪水印
        font_wm = _load_font(14, "sans")
        draw.text((self.MARGIN + 50, self.CANVAS_H - self.MARGIN - 50),
                  "【测试样张 - OCR测试数据】", fill=(200, 180, 160), font=font_wm)

        self._add_paper_texture(img)
        return img

    def render_resignation_proof(self, profile: dict) -> Image.Image:
        """渲染离职证明"""
        img, draw = self._create_base()
        emp = profile["employment"]

        font_title = _load_font(32, "kai")
        _draw_text_centered(draw, "离职证明",
                           (self.MARGIN, self.MARGIN + 80, self.CANVAS_W - self.MARGIN, self.MARGIN + 130),
                           fill=(80, 30, 20), font=font_title)

        font_body = _load_font(22, "kai")
        body = (
            f"    兹证明 {profile['name']}（身份证号：{profile['id_number']}），"
            f"于 {emp['hire_date']} 至 {emp['resign_date']} 在"
            f"我公司 {emp['department']} 担任 {emp['title']}。"
            f"该员工在职期间表现良好，工作认真负责。"
            f"因个人原因申请离职，现已办理完所有离职手续，"
            f"与我公司解除劳动关系。"
            f"特此证明。"
        )

        # 自动换行
        y = self.MARGIN + 220
        chars_per_line = 35
        for i in range(0, len(body), chars_per_line):
            line = body[i:i+chars_per_line]
            bbox = draw.textbbox((0, 0), line, font=font_body)
            x = (self.CANVAS_W - bbox[2] + bbox[0]) / 2
            draw.text((x, y), line, fill=(40, 30, 20), font=font_body)
            y += 45

        font_small = _load_font(18, "kai")
        draw.text((self.CANVAS_W - self.MARGIN - 300, self.CANVAS_H - self.MARGIN - 180),
                  f"{emp['company']}", fill=(60, 50, 40), font=font_small)
        draw.text((self.CANVAS_W - self.MARGIN - 300, self.CANVAS_H - self.MARGIN - 130),
                  f"{emp['resign_date']}", fill=(60, 50, 40), font=font_small)

        # 公章
        seal_cx = self.CANVAS_W - self.MARGIN - 180
        seal_cy = self.CANVAS_H - self.MARGIN - 110
        draw.ellipse([seal_cx - 70, seal_cy - 70, seal_cx + 70, seal_cy + 70],
                     outline=(200, 50, 50), width=4)
        font_seal = _load_font(16, "sans")
        _draw_text_centered(draw, emp["company"][:8],
                           (seal_cx - 55, seal_cy - 30, seal_cx + 55, seal_cy + 30),
                           fill=(200, 50, 50), font=font_seal)

        self._add_paper_texture(img)
        return img

    def render_employment_booklet(self, profile: dict) -> Image.Image:
        """渲染劳动手册/就业创业证"""
        img, draw = self._create_base()
        emp = profile["employment"]

        font_title = _load_font(30, "kai")
        _draw_text_centered(draw, "劳动手册（就业创业证）",
                           (self.MARGIN, self.MARGIN + 80, self.CANVAS_W - self.MARGIN, self.MARGIN + 130),
                           fill=(80, 30, 20), font=font_title)

        font_body = _load_font(20, "kai")
        items = [
            ("姓名", profile["name"]),
            ("性别", profile["gender"]),
            ("身份证号", profile["id_number"]),
            ("出生日期", profile["birth_date"]),
            ("学历", profile["education"]["level"]),
            ("就业单位", emp["company"]),
            ("岗位", emp["title"]),
            ("入职日期", emp["hire_date"]),
            ("离职日期", emp["resign_date"]),
        ]

        y = self.MARGIN + 200
        for label, value in items:
            draw.text((self.MARGIN + 100, y), f"{label}：", fill=(60, 50, 40), font=font_body)
            draw.text((self.MARGIN + 280, y), value, fill=(20, 20, 20), font=font_body)
            # 下划线
            draw.line([(self.MARGIN + 280, y + 32), (self.CANVAS_W - self.MARGIN - 80, y + 32)],
                      fill=(180, 170, 150), width=1)
            y += 55

        self._add_paper_texture(img)
        return img

    def _add_paper_texture(self, img: Image.Image):
        """添加纸张纹理噪点"""
        pixels = img.load()
        w, h = img.size
        for _ in range(w * h // 800):
            x = self.rng.randint(self.MARGIN, w - self.MARGIN)
            y = self.rng.randint(self.MARGIN, h - self.MARGIN)
            r, g, b = pixels[x, y]
            c = self.rng.randint(-6, 6)
            pixels[x, y] = (
                max(0, min(255, r + c)),
                max(0, min(255, g + c)),
                max(0, min(255, b + c)),
            )




