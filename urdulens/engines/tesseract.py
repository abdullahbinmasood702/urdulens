"""Tesseract engine (via pytesseract) using the Urdu ('urd') language data."""

from __future__ import annotations

import os
import shutil

from PIL import Image, ImageOps

from urdulens.engines.base import OCREngine

_WINDOWS_DEFAULT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def _configure_binary(pytesseract) -> None:
    """Point pytesseract at the binary: TESSERACT_CMD env var, PATH, or the Windows default."""
    custom = os.environ.get("TESSERACT_CMD")
    if custom:
        pytesseract.pytesseract.tesseract_cmd = custom
    elif not shutil.which("tesseract") and os.path.exists(_WINDOWS_DEFAULT):
        pytesseract.pytesseract.tesseract_cmd = _WINDOWS_DEFAULT


class TesseractEngine(OCREngine):
    name = "tesseract"

    def __init__(self, lang: str = "urd"):
        import pytesseract

        _configure_binary(pytesseract)
        self._pt = pytesseract
        self.lang = lang

    @classmethod
    def is_available(cls) -> tuple[bool, str]:
        try:
            import pytesseract
        except ImportError:
            return False, "pytesseract is not installed (pip install pytesseract)"
        _configure_binary(pytesseract)
        try:
            langs = pytesseract.get_languages(config="")
        except Exception as exc:  # binary missing or not runnable
            return False, f"Tesseract binary not found or not runnable: {exc}"
        if "urd" not in langs:
            return False, "Tesseract is installed but the Urdu data ('urd') is missing"
        return True, "ok"

    def version(self) -> str:
        return str(self._pt.get_tesseract_version())

    def _prep(self, image: Image.Image) -> Image.Image:
        # A white border noticeably helps Tesseract on tightly cropped lines.
        return ImageOps.expand(image.convert("L"), border=20, fill=255)

    def read_line(self, image: Image.Image) -> str:
        text = self._pt.image_to_string(self._prep(image), lang=self.lang, config="--psm 7")
        return " ".join(text.split())

    def read_document(self, image: Image.Image) -> str:
        text = self._pt.image_to_string(self._prep(image), lang=self.lang, config="--psm 6")
        return "\n".join(line.strip() for line in text.splitlines() if line.strip())
