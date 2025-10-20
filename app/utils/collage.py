from typing import List, Tuple
from PIL import Image


def _center_crop_to_square(img: Image.Image) -> Image.Image:
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    right = left + side
    bottom = top + side
    return img.crop((left, top, right, bottom))


def make_3x3_collage(image_paths: List[str], output_path: str, size: Tuple[int, int] = (1080, 1080)) -> None:
    """
    Create a 3x3 collage from up to 9 images. If fewer than 9, images are repeated to fill the grid.
    - size: final collage size (width, height), default 1080x1080 suitable for social posts.
    """
    if not image_paths:
        raise ValueError("image_paths must not be empty")

    # Limit to max 9, and repeat if fewer
    imgs = image_paths[:9]
    if len(imgs) < 9:
        # repeat images to fill
        reps = 9 - len(imgs)
        imgs = imgs + (imgs * ((reps + len(imgs) - 1) // len(imgs)))[:reps]

    collage = Image.new("RGB", size, (255, 255, 255))
    tile_w = size[0] // 3
    tile_h = size[1] // 3

    for i, path in enumerate(imgs[:9]):
        try:
            img = Image.open(path).convert("RGB")
        except Exception:
            # If an image fails to open, use a blank tile
            img = Image.new("RGB", (tile_w, tile_h), (240, 240, 240))

        img = _center_crop_to_square(img)
        img = img.resize((tile_w, tile_h), Image.LANCZOS)

        row = i // 3
        col = i % 3
        collage.paste(img, (col * tile_w, row * tile_h))

    collage.save(output_path, format="JPEG", quality=90)