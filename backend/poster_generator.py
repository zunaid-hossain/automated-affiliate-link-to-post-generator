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


def _fit_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:3]


def _rounded_rect_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def generate_poster(
    image_bytes: bytes,
    product_title: str = "",
    price: str = "",
    offer: str = "",
    cta_text: str = "Order Now",
) -> str:
    product = Image.open(__import__("io").BytesIO(image_bytes)).convert("RGBA")

    canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), "#f7f4ef")
    draw = ImageDraw.Draw(canvas)

    for y in range(CANVAS_SIZE):
        ratio = y / CANVAS_SIZE
        r = int(247 - ratio * 18)
        g = int(244 - ratio * 10)
        b = int(239 + ratio * 8)
        draw.line([(0, y), (CANVAS_SIZE, y)], fill=(r, g, b, 255))

    draw.ellipse((-140, 120, 300, 560), fill=(232, 242, 233, 255))
    draw.ellipse((790, -120, 1240, 330), fill=(246, 226, 205, 255))
    draw.rounded_rectangle((78, 78, 1002, 1002), radius=44, outline=(25, 46, 54, 36), width=2)

    max_product_box = (690, 610)
    display = ImageOps.contain(product, max_product_box)
    product_x = (CANVAS_SIZE - display.width) // 2
    product_y = 205

    shadow = Image.new("RGBA", display.size, (0, 0, 0, 0))
    alpha = display.getchannel("A")
    shadow.putalpha(alpha)
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))
    shadow_canvas = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_canvas.alpha_composite(shadow, (product_x + 24, product_y + 34))
    canvas = Image.alpha_composite(canvas, shadow_canvas)
    canvas.alpha_composite(display, (product_x, product_y))

    draw = ImageDraw.Draw(canvas)
    title_font = _font(54, bold=True)
    price_font = _font(62, bold=True)
    cta_font = _font(36, bold=True)
    badge_font = _font(30, bold=True)

    title = product_title.strip() or "Featured Product"
    lines = _fit_text(draw, title, title_font, 860)
    text_y = 806
    for line in lines:
        box = draw.textbbox((0, 0), line, font=title_font)
        draw.text(((CANVAS_SIZE - (box[2] - box[0])) / 2, text_y), line, font=title_font, fill="#17262b")
        text_y += 62

    if price:
        price_box = draw.textbbox((0, 0), price, font=price_font)
        draw.text(((CANVAS_SIZE - (price_box[2] - price_box[0])) / 2, 925), price, font=price_font, fill="#0f766e")

    if offer:
        badge_text = offer[:34]
        badge_box = draw.textbbox((0, 0), badge_text, font=badge_font)
        badge_w = badge_box[2] - badge_box[0] + 54
        draw.rounded_rectangle((82, 104, 82 + badge_w, 164), radius=30, fill="#f97316")
        draw.text((109, 119), badge_text, font=badge_font, fill="white")

    cta = cta_text.strip() or "Order Now"
    cta_box = draw.textbbox((0, 0), cta, font=cta_font)
    cta_w = cta_box[2] - cta_box[0] + 78
    cta_x = CANVAS_SIZE - cta_w - 86
    draw.rounded_rectangle((cta_x, 104, cta_x + cta_w, 166), radius=31, fill="#17262b")
    draw.text((cta_x + 39, 119), cta, font=cta_font, fill="white")

    output_name = f"poster-{uuid4().hex}.png"
    output_path = OUTPUT_DIR / output_name
    canvas.convert("RGB").save(output_path, "PNG", optimize=True)
    return output_name
