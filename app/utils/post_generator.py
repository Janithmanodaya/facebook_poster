from typing import List, Tuple, Dict
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """
    Try to load a sane default font. Falls back to a basic PIL font if a system font
    isn't available in the environment.
    """
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/Library/Fonts/Arial.ttf",
        "arial.ttf",
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def _make_gradient_bg(size: Tuple[int, int], start=(24, 31, 44), end=(11, 13, 18)) -> Image.Image:
    """
    Create a subtle vertical gradient background suitable for professional social posts.
    """
    w, h = size
    bg = Image.new("RGB", size, start)
    draw = ImageDraw.Draw(bg)
    for y in range(h):
        ratio = y / max(h - 1, 1)
        r = int(start[0] * (1 - ratio) + end[0] * ratio)
        g = int(start[1] * (1 - ratio) + end[1] * ratio)
        b = int(start[2] * (1 - ratio) + end[2] * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return bg


def _round_rect(img: Image.Image, radius: int) -> Image.Image:
    """
    Apply rounded corners to an image.
    """
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (w, h)], radius=radius, fill=255)
    out = Image.new("RGB", (w, h))
    out.paste(img, (0, 0), mask)
    return out


def _shadow(img: Image.Image, offset=(0, 4), blur_radius=16, opacity=120) -> Image.Image:
    """
    Add a drop shadow to an image.
    """
    w, h = img.size
    shadow = Image.new("RGBA", (w + abs(offset[0]) + blur_radius * 2, h + abs(offset[1]) + blur_radius * 2), (0, 0, 0, 0))
    shadow_layer = Image.new("RGBA", shadow.size, (0, 0, 0, 0))
    shadow_img = Image.new("RGBA", (w, h), (0, 0, 0, opacity))
    shadow_layer.paste(shadow_img, (blur_radius + max(offset[0], 0), blur_radius + max(offset[1], 0)))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur_radius))
    base = Image.new("RGBA", shadow.size, (0, 0, 0, 0))
    base.alpha_composite(shadow_layer)
    return base


def _fit_image(img: Image.Image, target_box: Tuple[int, int]) -> Image.Image:
    """
    Fit image into target_box preserving aspect ratio; center-crop if needed to fill.
    """
    tw, th = target_box
    iw, ih = img.size
    scale = max(tw / iw, th / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    resized = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return resized.crop((left, top, left + tw, top + th))


def generate_post_images(
    image_paths: List[str],
    out_dir: str,
    context: Dict[str, str],
) -> Dict[str, str]:
    """
    Generate multiple professional social post designs in different sizes.
    Returns a dict of {name: saved_path}.

    Designs:
      - modern_square_1080 (1080x1080) — hero image + info card
      - portrait_1200x1500 (1200x1500) — hero image top, details bottom
      - link_1200x628 (1200x628) — wide banner
    """
    os.makedirs(out_dir, exist_ok=True)
    if not image_paths:
        raise ValueError("No images provided")

    # Load first image as hero
    try:
        hero = Image.open(image_paths[0]).convert("RGB")
    except Exception:
        hero = Image.new("RGB", (1600, 1200), (30, 35, 45))

    # Common text
    model = context.get("model", "")
    year = context.get("manufacture_year", "")
    price = context.get("price", "")
    location = context.get("location", "")
    price_type = context.get("price_type", "")
    phone = context.get("phone", "")
    condition = context.get("condition", "")
    site_name = context.get("site_name", "Ganudenu.store")

    title_font = _load_font(64)
    subtitle_font = _load_font(36)
    small_font = _load_font(28)

    outputs: Dict[str, str] = {}

    # 1) Square modern 1080x1080
    size = (1080, 1080)
    bg = _make_gradient_bg(size, start=(21, 27, 36), end=(10, 12, 18))
    canvas = bg.copy()

    # left hero with rounded card + shadow
    hero_box = (640, 640)
    hero_img = _fit_image(hero, hero_box)
    hero_img = _round_rect(hero_img, 28)

    # Shadow
    sh = _shadow(hero_img, offset=(0, 12), blur_radius=32, opacity=110)
    sh_x = 80
    sh_y = 140
    base_rgba = Image.new("RGBA", canvas.size)
    base_rgba.paste(canvas.convert("RGBA"), (0, 0))
    base_rgba.alpha_composite(sh, dest=(sh_x - 16, sh_y - 4))
    base_rgba.alpha_composite(hero_img.convert("RGBA"), dest=(sh_x, sh_y))
    canvas = base_rgba.convert("RGB")

    # Right info panel
    draw = ImageDraw.Draw(canvas)
    info_x = 760
    info_y = 160
    # Title
    title = f"{model} {year}".strip()
    draw.text((info_x, info_y), title, font=title_font, fill=(229, 231, 235))
    info_y += 88
    # Price
    draw.text((info_x, info_y), f"Price: {price} ({price_type})", font=subtitle_font, fill=(156, 163, 175))
    info_y += 50
    # Condition
    draw.text((info_x, info_y), f"Condition: {condition}", font=subtitle_font, fill=(156, 163, 175))
    info_y += 50
    # Location
    draw.text((info_x, info_y), f"Location: {location}", font=subtitle_font, fill=(156, 163, 175))
    info_y += 50
    # Phone
    draw.text((info_x, info_y), f"Contact: {phone}", font=subtitle_font, fill=(156, 163, 175))

    # Badge / branding
    draw.rounded_rectangle([(60, 60), (320, 120)], radius=18, fill=(59, 130, 246))
    draw.text((76, 70), site_name, font=small_font, fill=(255, 255, 255))

    name = "modern_square_1080.jpg"
    path = os.path.join(out_dir, name)
    canvas.save(path, format="JPEG", quality=90)
    outputs["modern_square_1080"] = path

    # 2) Portrait 1200x1500
    size = (1200, 1500)
    bg = _make_gradient_bg(size, start=(21, 27, 36), end=(10, 12, 18))
    canvas = bg.copy()
    draw = ImageDraw.Draw(canvas)

    hero_box = (1100, 900)
    hero_img = _fit_image(hero, hero_box)
    hero_img = _round_rect(hero_img, 24)
    sh = _shadow(hero_img, offset=(0, 10), blur_radius=28, opacity=110)
    base_rgba = Image.new("RGBA", canvas.size)
    base_rgba.paste(canvas.convert("RGBA"), (0, 0))
    base_rgba.alpha_composite(sh, dest=(50, 90))
    base_rgba.alpha_composite(hero_img.convert("RGBA"), dest=(60, 100))
    canvas = base_rgba.convert("RGB")

    # Info band
    band_top = 1050
    draw.rounded_rectangle([(60, band_top), (1140, 1420)], radius=22, fill=(24, 31, 44))
    draw.text((90, band_top + 40), f"{model} {year}", font=title_font, fill=(229, 231, 235))
    draw.text((90, band_top + 110), f"{price} ({price_type})", font=subtitle_font, fill=(156, 163, 175))
    draw.text((90, band_top + 160), f"{condition} • {location}", font=subtitle_font, fill=(156, 163, 175))
    draw.text((90, band_top + 210), f"Contact: {phone}", font=subtitle_font, fill=(156, 163, 175))

    # Branding
    draw.text((940, band_top + 210), site_name, font=small_font, fill=(99, 102, 241))

    name = "portrait_1200x1500.jpg"
    path = os.path.join(out_dir, name)
    canvas.save(path, format="JPEG", quality=90)
    outputs["portrait_1200x1500"] = path

    # 3) Link banner 1200x628
    size = (1200, 628)
    bg = _make_gradient_bg(size, start=(21, 27, 36), end=(10, 12, 18))
    canvas = bg.copy()
    draw = ImageDraw.Draw(canvas)

    hero_box = (760, 560)
    hero_img = _fit_image(hero, hero_box)
    hero_img = _round_rect(hero_img, 22)
    sh = _shadow(hero_img, offset=(0, 8), blur_radius=22, opacity=110)
    base_rgba = Image.new("RGBA", canvas.size)
    base_rgba.paste(canvas.convert("RGBA"), (0, 0))
    base_rgba.alpha_composite(sh, dest=(40, 34))
    base_rgba.alpha_composite(hero_img.convert("RGBA"), dest=(50, 40))
    canvas = base_rgba.convert("RGB")

    # Right panel
    draw.text((840, 60), f"{model} {year}", font=title_font, fill=(229, 231, 235))
    draw.text((840, 140), f"{price} ({price_type})", font=subtitle_font, fill=(156, 163, 175))
    draw.text((840, 190), f"{condition}", font=subtitle_font, fill=(156, 163, 175))
    draw.text((840, 240), f"{location}", font=subtitle_font, fill=(156, 163, 175))
    draw.rounded_rectangle([(840, 300), (1140, 360)], radius=18, fill=(59, 130, 246))
    draw.text((860, 312), f"Call {phone}", font=small_font, fill=(255, 255, 255))

    name = "link_1200x628.jpg"
    path = os.path.join(out_dir, name)
    canvas.save(path, format="JPEG", quality=90)
    outputs["link_1200x628"] = path

    return outputs