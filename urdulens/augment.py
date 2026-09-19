"""Image degradations that imitate photos and scans of printed Urdu.

Three named levels are used by the benchmark:

* clean - rendered text with a little margin, no degradation
* mild  - slight blur, noise, tilt and JPEG compression (a decent phone photo)
* heavy - low resolution, strong blur/noise, shear, uneven light, heavy JPEG

Everything takes a numpy Generator so results are reproducible from a seed.
"""

from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageFilter

LEVELS = ("clean", "mild", "heavy")


def _jpeg(img: Image.Image, quality: int) -> Image.Image:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=int(quality))
    buf.seek(0)
    return Image.open(buf).convert("L")


def _illumination(img: Image.Image, rng: np.random.Generator, strength: float) -> Image.Image:
    """Multiply by a smooth brightness gradient (uneven lighting)."""
    w, h = img.size
    angle = rng.uniform(0, 2 * np.pi)
    xs = np.linspace(-1, 1, w)[None, :]
    ys = np.linspace(-1, 1, h)[:, None]
    grad = np.cos(angle) * xs + np.sin(angle) * ys
    factor = 1.0 - strength * (grad + 1) / 2
    arr = np.asarray(img, dtype=np.float32) * factor
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "L")


def _noise(img: Image.Image, rng: np.random.Generator, sigma: float) -> Image.Image:
    arr = np.asarray(img, dtype=np.float32)
    arr = arr + rng.normal(0, sigma, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "L")


def _rotate(img: Image.Image, degrees: float, fill: int) -> Image.Image:
    return img.rotate(degrees, resample=Image.BICUBIC, expand=True, fillcolor=fill)


def _shear(img: Image.Image, shear: float, fill: int) -> Image.Image:
    w, h = img.size
    extra = int(abs(shear) * h)
    offset = extra if shear > 0 else 0
    return img.transform(
        (w + extra, h),
        Image.AFFINE,
        (1, shear, -offset, 0, 1, 0),
        resample=Image.BICUBIC,
        fillcolor=fill,
    )


def _lowres(img: Image.Image, factor: float) -> Image.Image:
    w, h = img.size
    small = img.resize((max(8, int(w * factor)), max(8, int(h * factor))), Image.BILINEAR)
    return small.resize((w, h), Image.BILINEAR)


def degrade(img: Image.Image, level: str, rng: np.random.Generator) -> Image.Image:
    """Apply a named degradation level to a grayscale line image."""
    if level not in LEVELS:
        raise ValueError(f"level must be one of {LEVELS}, got {level!r}")
    img = img.convert("L")
    if level == "clean":
        return img
    bg = int(np.median(np.asarray(img)))
    if level == "mild":
        img = _rotate(img, rng.uniform(-1.5, 1.5), bg)
        img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0.3, 0.8)))
        img = _illumination(img, rng, rng.uniform(0.0, 0.15))
        img = _noise(img, rng, rng.uniform(3, 8))
        return _jpeg(img, rng.integers(70, 92))
    # heavy
    img = _rotate(img, rng.uniform(-3.0, 3.0), bg)
    img = _shear(img, rng.uniform(-0.12, 0.12), bg)
    img = _lowres(img, rng.uniform(0.45, 0.7))
    img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0.8, 1.6)))
    img = _illumination(img, rng, rng.uniform(0.15, 0.4))
    img = _noise(img, rng, rng.uniform(8, 16))
    return _jpeg(img, rng.integers(35, 60))
