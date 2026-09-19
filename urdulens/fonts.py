"""Fonts used to render synthetic Urdu text.

All bundled fonts are SIL Open Font License 1.1 (see fonts/OFL-*.txt).
Real-world Urdu print is mostly Nastaliq. Jameel Noori Nastaleeq, the font used
by most Pakistani newspapers and websites, is NOT openly licensed and is
therefore not bundled; Noto Nastaliq Urdu and Gulzar are the closest open
substitutes. Naskh fonts are included because Urdu also appears in Naskh
(user interfaces, some books) and because Arabic-trained OCR engines expect it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import ImageFont

from urdulens.paths import FONT_DIR


@dataclass(frozen=True)
class FontSpec:
    key: str
    filename: str
    style: str  # "nastaliq" or "naskh"
    size_range: tuple[int, int]  # pixel sizes sampled for rendering
    weights: tuple[int, ...] = ()  # variable-font weights to sample (empty = static font)

    @property
    def path(self) -> Path:
        return FONT_DIR / self.filename


FONTS: dict[str, FontSpec] = {
    f.key: f
    for f in [
        FontSpec("noto-nastaliq", "NotoNastaliqUrdu.ttf", "nastaliq", (34, 52), (400, 500, 700)),
        FontSpec("gulzar", "Gulzar-Regular.ttf", "nastaliq", (34, 52)),
        FontSpec("lateef", "Lateef-Regular.ttf", "naskh", (46, 66)),
        FontSpec("noto-naskh", "NotoNaskhArabic.ttf", "naskh", (34, 50), (400, 500, 700)),
        FontSpec("scheherazade", "ScheherazadeNew-Regular.ttf", "naskh", (34, 50)),
    ]
}
FONT_KEYS = tuple(FONTS)


def available_fonts() -> list[str]:
    return [k for k, f in FONTS.items() if f.path.exists()]


def load_font(key: str, size: int, weight: int | None = None) -> ImageFont.FreeTypeFont:
    """Load a font with the RAQM layout engine (needed for correct Urdu shaping)."""
    spec = FONTS[key]
    if not spec.path.exists():
        raise FileNotFoundError(f"Font file missing: {spec.path}")
    font = ImageFont.truetype(str(spec.path), size, layout_engine=ImageFont.Layout.RAQM)
    if weight is not None and spec.weights:
        font.set_variation_by_axes([weight])
    return font
