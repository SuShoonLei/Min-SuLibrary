#!/usr/bin/env python3
"""Build the smaller logo files the pages actually load.

The source is public/assets/brand/logo.png. From the project root:

    python scripts/make_brand_assets.py

Colors below were sampled from that PNG: the cloud is #C2E0EA, the banner
is #F8BDB2, and the lettering is #232C4B.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "public" / "assets" / "brand"
SOURCE = BRAND / "logo.png"

# The pastel cloud, sampled from the opaque pixels behind the couple.
SKY = (194, 224, 234, 255)


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"Missing source logo: {SOURCE}")

    logo = Image.open(SOURCE).convert("RGBA")
    for size in (400, 800, 1200):
        resized = _resize_rgba(logo, size)
        resized.save(
            BRAND / f"logo-{size}.webp",
            "WEBP",
            lossless=True,
            exact=True,
            quality=100,
            method=6,
        )

    mark = _face_mark(logo)
    mark.resize((32, 32), Image.Resampling.LANCZOS).save(BRAND / "favicon-32.png", "PNG")
    mark.resize((180, 180), Image.Resampling.LANCZOS).save(BRAND / "favicon-180.png", "PNG")

    og = Image.new("RGB", (1200, 630), SKY[:3])
    fitted = logo.copy()
    fitted.thumbnail((520, 520), Image.Resampling.LANCZOS)
    left = (og.width - fitted.width) // 2
    top = (og.height - fitted.height) // 2
    og.paste(fitted, (left, top), fitted)
    og.save(BRAND / "og-image.png", "PNG")

    print("Wrote logo webp files, favicons, and og-image.png in public/assets/brand/")


def _resize_rgba(logo: Image.Image, size: int) -> Image.Image:
    """Scale the logo without turning transparent pixels into a white square.

    Fully transparent pixels in the source still store a near-white color.
    A normal resize blends that white in. Premultiplying by alpha first
    keeps those pixels clear, and the WebP is saved lossless with its alpha.
    """
    red, green, blue, alpha = logo.split()
    premultiplied = Image.merge(
        "RGBA",
        (
            ImageChops.multiply(red, alpha),
            ImageChops.multiply(green, alpha),
            ImageChops.multiply(blue, alpha),
            alpha,
        ),
    )
    resized = premultiplied.resize((size, size), Image.Resampling.LANCZOS)
    pixels = resized.load()
    width, height = resized.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                pixels[x, y] = (0, 0, 0, 0)
            elif a < 255:
                pixels[x, y] = (
                    min(255, round(r * 255 / a)),
                    min(255, round(g * 255 / a)),
                    min(255, round(b * 255 / a)),
                    a,
                )
    return resized


def _face_mark(logo: Image.Image) -> Image.Image:
    """The couple and the cloud, without the pink name banner, on sky blue.

    The banner sits in the bottom of the square. Cutting there keeps the
    faces and the cloud for the home-screen icon.
    """
    banner_cut = int(logo.height * 0.78)
    cropped = logo.crop((0, 0, logo.width, banner_cut))
    alpha = cropped.getchannel("A")
    mask = alpha.point(lambda value: 255 if value > 16 else 0)
    bbox = mask.getbbox()
    if bbox:
        cropped = cropped.crop(bbox)

    side = int(max(cropped.size) * 1.12)
    canvas = Image.new("RGBA", (side, side), SKY)
    left = (side - cropped.width) // 2
    top = (side - cropped.height) // 2
    canvas.paste(cropped, (left, top), cropped)
    return canvas


if __name__ == "__main__":
    main()
