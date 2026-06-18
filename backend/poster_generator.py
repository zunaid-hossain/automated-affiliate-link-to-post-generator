import colorsys
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

CANVAS_SIZE = 1080

RGB = tuple[int, int, int]
RGBA = tuple[int, int, int, int]


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def _poster_text(value: str) -> str:
    return value.replace("৳", "Tk ").strip()


def _rgba(color: RGB, alpha: int = 255) -> RGBA:
    return color[0], color[1], color[2], alpha


def _hex(color: RGB) -> str:
    return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"


def _mix(a: RGB, b: RGB, amount: float) -> RGB:
    return tuple(int(a[i] * (1 - amount) + b[i] * amount) for i in range(3))  # type: ignore[return-value]


def _relative_luminance(color: RGB) -> float:
    r, g, b = [value / 255 for value in color]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _saturate(color: RGB, factor: float = 1.35, light: float = 0.0) -> RGB:
    r, g, b = [value / 255 for value in color]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    s = max(0.35, min(1.0, s * factor))
    l = max(0.18, min(0.72, l + light))
    nr, ng, nb = colorsys.hls_to_rgb(h, l, s)
    return int(nr * 255), int(ng * 255), int(nb * 255)


def _complement(color: RGB) -> RGB:
    r, g, b = [value / 255 for value in color]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    nr, ng, nb = colorsys.hls_to_rgb((h + 0.5) % 1.0, max(0.34, min(0.58, l)), max(0.55, s))
    return int(nr * 255), int(ng * 255), int(nb * 255)


def _dominant_color(product: Image.Image) -> RGB:
    image = Image.new("RGBA", product.size, "#ffffff")
    image.alpha_composite(product)
    image = image.convert("RGB").resize((80, 80))
    colors = image.quantize(colors=8, method=0).convert("RGB").getcolors(6400) or []
    scored: list[tuple[float, RGB]] = []
    for count, color in colors:
        r, g, b = color
        luminance = _relative_luminance(color)
        spread = max(color) - min(color)
        if luminance > 0.92 or luminance < 0.06 or spread < 18:
            continue
        saturation_bonus = spread / 255
        scored.append((count * (0.65 + saturation_bonus), color))
    if not scored:
        return 45, 212, 191
    scored.sort(reverse=True, key=lambda item: item[0])
    return _saturate(scored[0][1], 1.45, 0.02)


def _palette(product: Image.Image, product_title: str, category: str = "") -> dict[str, RGB]:
    text = f"{product_title} {category}".lower()
    dominant = _dominant_color(product)
    palettes: dict[str, dict[str, RGB]] = {
        "food": {"dark": (42, 5, 5), "panel": (130, 10, 10), "accent": (239, 40, 30), "accent2": (255, 207, 51)},
        "fashion": {"dark": (20, 35, 24), "panel": (236, 197, 0), "accent": (255, 211, 0), "accent2": (31, 107, 64)},
        "shoe": {"dark": (11, 10, 24), "panel": (88, 28, 135), "accent": (217, 70, 239), "accent2": (163, 230, 53)},
        "electronics": {"dark": (5, 16, 33), "panel": (8, 47, 73), "accent": (6, 182, 212), "accent2": (96, 165, 250)},
        "beauty": {"dark": (45, 15, 32), "panel": (131, 24, 67), "accent": (244, 114, 182), "accent2": (251, 191, 36)},
    }
    keyword_map = {
        "food": ["food", "burger", "ketchup", "tomato", "chicken", "snack", "drink", "restaurant", "pizza"],
        "fashion": ["fashion", "shirt", "dress", "watch", "bag", "clothing", "style", "wear"],
        "shoe": ["shoe", "sneaker", "trainer", "nike", "adidas", "footwear"],
        "electronics": ["phone", "speaker", "earbud", "gadget", "electronic", "laptop", "camera", "watch", "smart"],
        "beauty": ["beauty", "makeup", "skin", "cream", "serum", "perfume", "cosmetic"],
    }
    selected = ""
    for name, words in keyword_map.items():
        if any(word in text for word in words):
            selected = name
            break
    if selected:
        return palettes[selected]
    accent = dominant
    accent2 = _complement(accent)
    dark = _mix(accent, (3, 10, 20), 0.82)
    panel = _mix(accent2, (10, 20, 35), 0.42)
    if _relative_luminance(accent2) < 0.4:
        accent2 = _saturate(accent2, 1.25, 0.16)
    return {"dark": dark, "panel": panel, "accent": accent, "accent2": accent2}


def _fit_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int, max_lines: int = 3) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if _text_size(draw, test, font)[0] <= width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:max_lines]


def _fit_font(draw: ImageDraw.ImageDraw, text: str, width: int, start: int, minimum: int = 34) -> ImageFont.ImageFont:
    for size in range(start, minimum - 1, -3):
        font = _font(size, bold=True)
        if all(_text_size(draw, line, font)[0] <= width for line in _fit_text(draw, text, font, width, 2)):
            return font
    return _font(minimum, bold=True)


def _draw_text_with_shadow(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: str,
    stroke_fill: str = "#07111f",
    stroke_width: int = 4,
) -> None:
    x, y = xy
    draw.text((x + 6, y + 7), text, font=font, fill=(0, 0, 0, 150), stroke_width=stroke_width, stroke_fill=(0, 0, 0, 150))
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)


def _alpha_shadow(image: Image.Image, offset: tuple[int, int], blur: int, opacity: int) -> Image.Image:
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow.putalpha(image.getchannel("A").point(lambda value: min(value, opacity)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    layer = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    layer.alpha_composite(shadow, offset)
    return layer


def generate_poster(
    image_bytes: bytes,
    product_title: str = "",
    price: str = "",
    offer: str = "",
    cta_text: str = "Order Now",
    category: str = "",
) -> str:
    product = Image.open(__import__("io").BytesIO(image_bytes)).convert("RGBA")

    title = _poster_text(product_title) or "Featured Product"
    price = _poster_text(price)
    offer = _poster_text(offer)
    cta = _poster_text(cta_text) or "Order Now"
    palette = _palette(product, title, category)
    dark = palette["dark"]
    panel = palette["panel"]
    accent = palette["accent"]
    accent2 = palette["accent2"]
    text_dark = _mix(dark, (0, 0, 0), 0.2)

    base = Image.new("RGBA", product.size, "#f7f7f7")
    base.alpha_composite(product)
    bg = ImageOps.fit(base.convert("RGB"), (CANVAS_SIZE, CANVAS_SIZE)).convert("RGBA")
    bg = bg.filter(ImageFilter.GaussianBlur(30))
    canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), _hex(dark))
    canvas.alpha_composite(bg)

    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rectangle((0, 0, CANVAS_SIZE, CANVAS_SIZE), fill=_rgba(dark, 182))
    draw.polygon([(0, 0), (650, 0), (470, 1080), (0, 1080)], fill=_rgba(_mix(dark, (0, 0, 0), 0.28), 218))
    draw.polygon([(705, 0), (1080, 0), (1080, 1080), (870, 1080)], fill=_rgba(panel, 192))
    draw.polygon([(0, 820), (1080, 660), (1080, 1080), (0, 1080)], fill=(255, 255, 255, 24))

    for x in range(44, 528, 38):
        for y in range(96, 370, 38):
            draw.ellipse((x, y, x + 4, y + 4), fill=(255, 255, 255, 72))
    for y in range(430, 760, 44):
        draw.line((62, y, 402, y - 44), fill=_rgba(accent, 56), width=3)

    draw.line((62, 76, 390, 76), fill=_rgba(accent, 255), width=6)
    draw.text((64, 100), "FEATURED DEAL", font=_font(28, bold=True), fill=_rgba(accent, 255))

    title_font = _fit_font(draw, title.upper(), 470, 76, 42)
    title_lines = _fit_text(draw, title.upper(), title_font, 470, 3)
    title_y = 158
    for line in title_lines:
        _draw_text_with_shadow(draw, (62, title_y), line, title_font, "#ffffff", _hex(text_dark), 3)
        title_y += _text_size(draw, line, title_font)[1] + 12

    sub_font = _font(25, bold=True)
    draw.line((64, title_y + 30, 362, title_y + 30), fill=_rgba(accent, 230), width=4)
    draw.text((64, title_y + 44), "LIMITED TIME OFFER", font=sub_font, fill=(255, 255, 255, 230))

    max_product_box = (610, 680)
    display = ImageOps.contain(product, max_product_box)
    product_x = 436 + max(0, (590 - display.width) // 2)
    product_y = 252 + max(0, (632 - display.height) // 2)

    halo = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    halo_draw = ImageDraw.Draw(halo, "RGBA")
    halo_draw.ellipse((374, 210, 1054, 900), fill=(255, 255, 255, 68))
    halo_draw.ellipse((432, 268, 1000, 846), outline=_rgba(accent, 155), width=8)
    halo = halo.filter(ImageFilter.GaussianBlur(10))
    canvas.alpha_composite(halo)
    canvas.alpha_composite(_alpha_shadow(display, (product_x + 26, product_y + 36), 28, 185))
    canvas.alpha_composite(display, (product_x, product_y))

    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle((52, 828, 548, 1012), radius=16, fill=(255, 255, 255, 238))
    draw.rectangle((52, 828, 84, 1012), fill=_rgba(accent, 255))
    draw.line((100, 874, 500, 874), fill=_rgba(dark, 38), width=2)

    if price:
        draw.text((110, 858), "TODAY PRICE", font=_font(24, bold=True), fill=_rgba(_mix(accent, dark, 0.25), 255))
        price_font = _fit_font(draw, price, 380, 68, 42)
        draw.text((108, 902), price, font=price_font, fill=_rgba(accent2, 255), stroke_width=2, stroke_fill=_rgba(text_dark, 255))

    badge_text = (offer or "HOT DEAL").upper()[:24]
    badge_font = _fit_font(draw, badge_text, 270, 35, 24)
    badge_w, badge_h = _text_size(draw, badge_text, badge_font)
    draw.polygon([(728, 82), (1012, 112), (982, 226), (694, 194)], fill=_rgba(accent2, 250))
    draw.line([(728, 82), (1012, 112), (982, 226), (694, 194), (728, 82)], fill=(255, 255, 255, 230), width=4)
    badge_fill = "#ffffff" if _relative_luminance(accent2) < 0.58 else _hex(text_dark)
    draw.text((724 + (250 - badge_w) / 2, 124 + (54 - badge_h) / 2), badge_text, font=badge_font, fill=badge_fill, stroke_width=2, stroke_fill=_hex(text_dark))

    cta_font = _fit_font(draw, cta.upper(), 300, 40, 28)
    cta_w, cta_h = _text_size(draw, cta.upper(), cta_font)
    draw.rounded_rectangle((660, 908, 1014, 988), radius=40, fill=_rgba(accent2, 255))
    draw.rounded_rectangle((672, 920, 1002, 976), radius=28, outline=(255, 255, 255, 230), width=3)
    cta_fill = "#ffffff" if _relative_luminance(accent2) < 0.58 else _hex(text_dark)
    draw.text((660 + (354 - cta_w) / 2, 930 + (36 - cta_h) / 2), cta.upper(), font=cta_font, fill=cta_fill)

    draw.rounded_rectangle((642, 826, 990, 874), radius=24, fill=_rgba(_mix(dark, (0, 0, 0), 0.2), 188))
    draw.text((668, 838), "FAST ORDER VIA LINK", font=_font(24, bold=True), fill=(255, 255, 255, 230))

    output_name = f"poster-{uuid4().hex}.png"
    output_path = OUTPUT_DIR / output_name
    canvas.convert("RGB").save(output_path, "PNG", optimize=True)
    return output_name
