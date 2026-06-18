from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

CANVAS_SIZE = 1080


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
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
) -> str:
    product = Image.open(__import__("io").BytesIO(image_bytes)).convert("RGBA")

    title = _poster_text(product_title) or "Featured Product"
    price = _poster_text(price)
    offer = _poster_text(offer)
    cta = _poster_text(cta_text) or "Order Now"

    base = Image.new("RGBA", product.size, "#f7f7f7")
    base.alpha_composite(product)
    bg = ImageOps.fit(base.convert("RGB"), (CANVAS_SIZE, CANVAS_SIZE)).convert("RGBA")
    bg = bg.filter(ImageFilter.GaussianBlur(30))
    canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), "#07111f")
    canvas.alpha_composite(bg)

    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rectangle((0, 0, CANVAS_SIZE, CANVAS_SIZE), fill=(4, 12, 22, 176))
    draw.polygon([(0, 0), (650, 0), (470, 1080), (0, 1080)], fill=(7, 17, 31, 210))
    draw.polygon([(705, 0), (1080, 0), (1080, 1080), (870, 1080)], fill=(249, 115, 22, 178))
    draw.polygon([(0, 820), (1080, 660), (1080, 1080), (0, 1080)], fill=(255, 255, 255, 24))

    for x in range(44, 528, 38):
        for y in range(96, 370, 38):
            draw.ellipse((x, y, x + 4, y + 4), fill=(255, 255, 255, 72))
    for y in range(430, 760, 44):
        draw.line((62, y, 402, y - 44), fill=(45, 212, 191, 42), width=3)

    draw.line((62, 76, 390, 76), fill=(45, 212, 191, 255), width=6)
    draw.text((64, 100), "FEATURED DEAL", font=_font(28, bold=True), fill=(45, 212, 191, 255))

    title_font = _fit_font(draw, title.upper(), 470, 76, 42)
    title_lines = _fit_text(draw, title.upper(), title_font, 470, 3)
    title_y = 158
    for line in title_lines:
        _draw_text_with_shadow(draw, (62, title_y), line, title_font, "#ffffff", "#07111f", 3)
        title_y += _text_size(draw, line, title_font)[1] + 12

    sub_font = _font(25, bold=True)
    draw.line((64, title_y + 30, 362, title_y + 30), fill=(45, 212, 191, 230), width=4)
    draw.text((64, title_y + 44), "LIMITED TIME OFFER", font=sub_font, fill=(255, 255, 255, 230))

    max_product_box = (610, 680)
    display = ImageOps.contain(product, max_product_box)
    product_x = 436 + max(0, (590 - display.width) // 2)
    product_y = 252 + max(0, (632 - display.height) // 2)

    halo = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    halo_draw = ImageDraw.Draw(halo, "RGBA")
    halo_draw.ellipse((374, 210, 1054, 900), fill=(255, 255, 255, 68))
    halo_draw.ellipse((432, 268, 1000, 846), outline=(45, 212, 191, 150), width=8)
    halo = halo.filter(ImageFilter.GaussianBlur(10))
    canvas.alpha_composite(halo)
    canvas.alpha_composite(_alpha_shadow(display, (product_x + 26, product_y + 36), 28, 185))
    canvas.alpha_composite(display, (product_x, product_y))

    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle((52, 828, 548, 1012), radius=16, fill=(255, 255, 255, 238))
    draw.rectangle((52, 828, 84, 1012), fill=(45, 212, 191, 255))
    draw.line((100, 874, 500, 874), fill=(7, 17, 31, 35), width=2)

    if price:
        draw.text((110, 858), "TODAY PRICE", font=_font(24, bold=True), fill=(15, 118, 110, 255))
        price_font = _fit_font(draw, price, 380, 68, 42)
        draw.text((108, 902), price, font=price_font, fill=(249, 115, 22, 255), stroke_width=2, stroke_fill=(7, 17, 31, 255))

    badge_text = (offer or "HOT DEAL").upper()[:24]
    badge_font = _fit_font(draw, badge_text, 270, 35, 24)
    badge_w, badge_h = _text_size(draw, badge_text, badge_font)
    draw.polygon([(728, 82), (1012, 112), (982, 226), (694, 194)], fill=(249, 115, 22, 250))
    draw.line([(728, 82), (1012, 112), (982, 226), (694, 194), (728, 82)], fill=(255, 255, 255, 230), width=4)
    draw.text((724 + (250 - badge_w) / 2, 124 + (54 - badge_h) / 2), badge_text, font=badge_font, fill="#ffffff", stroke_width=2, stroke_fill="#7c2d12")

    cta_font = _fit_font(draw, cta.upper(), 300, 40, 28)
    cta_w, cta_h = _text_size(draw, cta.upper(), cta_font)
    draw.rounded_rectangle((660, 908, 1014, 988), radius=40, fill=(249, 115, 22, 255))
    draw.rounded_rectangle((672, 920, 1002, 976), radius=28, outline=(255, 255, 255, 230), width=3)
    draw.text((660 + (354 - cta_w) / 2, 930 + (36 - cta_h) / 2), cta.upper(), font=cta_font, fill="#ffffff")

    draw.rounded_rectangle((642, 826, 990, 874), radius=24, fill=(7, 17, 31, 176))
    draw.text((668, 838), "FAST ORDER VIA LINK", font=_font(24, bold=True), fill=(255, 255, 255, 230))

    output_name = f"poster-{uuid4().hex}.png"
    output_path = OUTPUT_DIR / output_name
    canvas.convert("RGB").save(output_path, "PNG", optimize=True)
    return output_name
