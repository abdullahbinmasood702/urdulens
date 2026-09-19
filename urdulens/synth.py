"""Synthetic Urdu line images: render text with a font, then degrade it."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw

from urdulens import augment, fonts


@dataclass(frozen=True)
class Sample:
    image: Image.Image
    text: str
    font: str
    style: str
    level: str


def render_line(
    text: str,
    font_key: str,
    size: int,
    weight: int | None = None,
    fg: int = 20,
    bg: int = 245,
    pad_x: int = 16,
    pad_y: int = 10,
) -> Image.Image:
    """Render one line of right-to-left Urdu text into a tight grayscale image."""
    font = fonts.load_font(font_key, size, weight)
    kwargs = dict(direction="rtl", language="ur", anchor="la")
    left, top, right, bottom = font.getbbox(text, **kwargs)
    width = int(right - left) + 2 * pad_x
    height = int(bottom - top) + 2 * pad_y
    img = Image.new("L", (max(width, 8), max(height, 8)), bg)
    ImageDraw.Draw(img).text((pad_x - left, pad_y - top), text, font=font, fill=fg, **kwargs)
    return img


def make_sample(
    rng: np.random.Generator,
    text: str,
    font_key: str | None = None,
    level: str = "mild",
    available: list[str] | None = None,
) -> Sample:
    """Render `text` with a (random) font and apply the requested degradation level."""
    pool = available or fonts.available_fonts()
    if not pool:
        raise FileNotFoundError("No fonts found. Expected files in the fonts/ folder.")
    key = font_key or pool[int(rng.integers(0, len(pool)))]
    spec = fonts.FONTS[key]
    size = int(rng.integers(spec.size_range[0], spec.size_range[1] + 1))
    weight = int(rng.choice(spec.weights)) if spec.weights else None
    bg = int(rng.integers(225, 256))
    fg = int(rng.integers(0, 60))
    pad_x = int(rng.integers(8, 28))
    pad_y = int(rng.integers(6, 18))
    img = render_line(text, key, size, weight, fg, bg, pad_x, pad_y)
    img = augment.degrade(img, level, rng)
    return Sample(image=img, text=text, font=key, style=spec.style, level=level)
