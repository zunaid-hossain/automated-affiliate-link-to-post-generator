import colorsys
import math
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


def _category_palette(product: Image.Image, product_title: str, category: str = "") -> dict[str, RGB]:
    text = f"{product_title} {category}".lower()
    if any(word in text for word in ["food", "burger", "ketchup", "tomato", "chicken", "snack", "drink", "pizza"]):
        return {"top": (156, 9, 14), "bottom": (239, 34, 24), "paint": (255, 207, 51), "accent": (255, 225, 74), "dark": (39, 8, 9)}
    if any(word in text for word in ["shoe", "sneaker", "trainer", "footwear", "nike", "adidas"]):
        return {"top": (11, 28, 32), "bottom": (12, 148, 136), "paint": (166, 230, 35), "accent": (217, 70, 239), "dark": (7, 12, 20)}
    if any(word in text for word in ["beauty", "makeup", "skin", "cream", "serum", "perfume", "cosmetic"]):
        return {"top": (118, 18, 76), "bottom": (236, 72, 153), "paint": (255, 205, 87), "accent": (255, 182, 193), "dark": (40, 10, 30)}
    if any(word in text for word in ["fashion", "shirt", "dress", "watch", "bag", "clothing", "style", "wear"]):
        return {"top": (14, 78, 62), "bottom": (22, 163, 74), "paint": (255, 207, 36), "accent": (255, 255, 255), "dark": (11, 41, 31)}

    dominant = _dominant_color(product)
    top = _mix(_saturate(dominant, 1.15, -0.04), (0, 95, 122), 0.72)
    bottom = _mix(_saturate(dominant, 1.35, 0.08), (8, 178, 206), 0.62)
    return {"top": top, "bottom": bottom, "paint": (255, 190, 24), "accent": (255, 226, 68), "dark": _mix(top, (0, 0, 0), 0.55)}


def _draw_reference_background(canvas: Image.Image, palette: dict[str, RGB]) -> None:
    draw = ImageDraw.Draw(canvas, "RGBA")
    top = palette["top"]
    bottom = palette["bottom"]
    center = (CANVAS_SIZE // 2, 624)

    for y in range(CANVAS_SIZE):
        ratio = y / CANVAS_SIZE
        color = _mix(top, bottom, ratio)
        draw.line((0, y, CANVAS_SIZE, y), fill=_rgba(color, 255))

    for angle in range(-30, 211, 14):
        length = 1500
        x = center[0] + int(length * math.cos(math.radians(angle)))
        y = center[1] + int(length * math.sin(math.radians(angle)))
        draw.polygon([center, (x - 18, y - 18), (x + 18, y + 18)], fill=(255, 255, 255, 13))

    for angle in range(220, 520, 18):
        length = 1500
        x = center[0] + int(length * math.cos(math.radians(angle)))
        y = center[1] + int(length * math.sin(math.radians(angle)))
        draw.line((center[0], center[1], x, y), fill=(255, 255, 255, 12), width=2)

    draw.rectangle((0, 0, CANVAS_SIZE, CANVAS_SIZE), outline=_rgba(_mix(top, (0, 0, 0), 0.35), 255), width=16)
    draw.polygon([(0, 700), (260, 626), (660, 725), (1080, 616), (1080, 1080), (0, 1080)], fill=_rgba(palette["paint"], 255))
    draw.polygon([(0, 676), (190, 628), (330, 670), (0, 764)], fill=_rgba(_mix(palette["dark"], (0, 0, 0), 0.1), 245))
    draw.polygon([(0, 810), (374, 718), (600, 748), (0, 908)], fill=_rgba(_mix(palette["dark"], (0, 0, 0), 0.12), 235))
    draw.polygon([(760, 634), (1080, 538), (1080, 640), (825, 700)], fill=_rgba(palette["paint"], 255))
    draw.polygon([(824, 666), (1080, 606), (1080, 664), (884, 716)], fill=_rgba(_mix(palette["dark"], (0, 0, 0), 0.05), 220))

    for box in [(90, 390, 150, 450), (806, 264, 852, 310), (845, 286, 904, 345)]:
        draw.ellipse(box, outline=(255, 255, 255, 92), width=3)

    for x in [850, 900, 950]:
        draw.ellipse((x, 116, x + 24, 140), outline=(255, 255, 255, 235), width=7)


def _draw_centered_text(draw: ImageDraw.ImageDraw, y: int, text: str, font: ImageFont.ImageFont, fill: str, stroke_fill: str | None = None, stroke_width: int = 0) -> int:
    width, height = _text_size(draw, text, font)
    draw.text(((CANVAS_SIZE - width) / 2, y), text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill or fill)
    return y + height


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
    palette = _category_palette(product, title, category)
    dark = palette["dark"]
    paint = palette["paint"]

    canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), _hex(palette["top"]))
    _draw_reference_background(canvas, palette)
    draw = ImageDraw.Draw(canvas, "RGBA")

    draw.text((88, 118), "DEAL", font=_font(28, bold=True), fill=(255, 255, 255, 230))
    script_font = _font(48, bold=False)
    _draw_centered_text(draw, 154, "The Best", script_font, "#ffffff")

    hero_font = _fit_font(draw, title.upper(), 740, 118, 70)
    title_lines = _fit_text(draw, title.upper(), hero_font, 740, 2)
    headline_y = 216
    if len(title_lines) > 1:
        hero_font = _fit_font(draw, title.upper(), 800, 94, 62)
    for line in title_lines:
        headline_y = _draw_centered_text(draw, headline_y, line, hero_font, "#ffffff", _hex(dark), 2) + 2

    subline = f"FOR YOUR {category.upper()}" if category else "FOR YOUR SHOPPING"
    sub_font = _fit_font(draw, subline, 420, 34, 22)
    _draw_centered_text(draw, headline_y + 10, subline, sub_font, "#ffffff")

    discount_text = offer.upper() if offer else "SPECIAL DEAL"
    discount_font = _fit_font(draw, discount_text, 260, 34, 23)
    discount_y = headline_y + 74
    discount_w, discount_h = _text_size(draw, discount_text, discount_font)
    draw.ellipse((CANVAS_SIZE / 2 - 118, discount_y - 20, CANVAS_SIZE / 2 + 118, discount_y + 86), fill=(255, 255, 255, 24), outline=(255, 255, 255, 130), width=3)
    draw.text(((CANVAS_SIZE - discount_w) / 2, discount_y + (52 - discount_h) / 2), discount_text, font=discount_font, fill="#ffffff", stroke_width=2, stroke_fill=_hex(dark))

    max_product_box = (660, 450)
    display = ImageOps.contain(product, max_product_box)
    product_x = (CANVAS_SIZE - display.width) // 2
    product_y = 594 + max(0, (260 - display.height) // 2)

    ellipse_layer = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    ellipse_draw = ImageDraw.Draw(ellipse_layer, "RGBA")
    ellipse_draw.ellipse((260, 742, 820, 885), fill=(0, 0, 0, 90))
    ellipse_layer = ellipse_layer.filter(ImageFilter.GaussianBlur(24))
    canvas.alpha_composite(ellipse_layer)
    canvas.alpha_composite(_alpha_shadow(display, (product_x + 20, product_y + 26), 22, 170))
    canvas.alpha_composite(display, (product_x, product_y))

    draw = ImageDraw.Draw(canvas, "RGBA")

    if price:
        price_font = _fit_font(draw, price, 220, 42, 28)
        price_w, price_h = _text_size(draw, price, price_font)
        draw.ellipse((774, 548, 930, 704), fill=_rgba(paint, 255))
        draw.ellipse((784, 558, 920, 694), outline=_rgba(dark, 170), width=3)
        draw.text((852 - price_w / 2, 586), price, font=price_font, fill=_hex(dark), stroke_width=1, stroke_fill="#ffffff")
        draw.text((820, 634), "PRICE", font=_font(22, bold=True), fill=_hex(dark))

    draw.rectangle((0, 940, CANVAS_SIZE, 1034), fill=(38, 31, 20, 126))
    draw.ellipse((98, 970, 150, 1022), fill="#ffffff")
    draw.text((174, 964), "ORDER FROM LINK", font=_font(26, bold=True), fill="#ffffff")
    draw.text((174, 996), "CHECK CAPTION FOR DETAILS", font=_font(24, bold=True), fill="#ffffff")

    cta_font = _fit_font(draw, cta.upper(), 210, 24, 18)
    cta_w, cta_h = _text_size(draw, cta.upper(), cta_font)
    draw.rounded_rectangle((748, 978, 934, 1018), radius=4, fill=(255, 255, 255, 245))
    draw.text((841 - cta_w / 2, 989 + (18 - cta_h) / 2), cta.upper(), font=cta_font, fill=_hex(dark))

    output_name = f"poster-{uuid4().hex}.png"
    output_path = OUTPUT_DIR / output_name
    canvas.convert("RGB").save(output_path, "PNG", optimize=True)
    return output_name
