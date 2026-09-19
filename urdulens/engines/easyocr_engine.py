"""EasyOCR engine (Urdu model 'ur')."""

from __future__ import annotations

import numpy as np
from PIL import Image

from urdulens.engines.base import OCREngine
from urdulens.layout import assemble_rtl


class EasyOCREngine(OCREngine):
    name = "easyocr"

    def __init__(self, gpu: bool = False):
        import easyocr

        self._reader = easyocr.Reader(["ur"], gpu=gpu, verbose=False)
        self._easyocr = easyocr

    @classmethod
    def is_available(cls) -> tuple[bool, str]:
        try:
            import easyocr  # noqa: F401
        except ImportError:
            return False, "easyocr is not installed (pip install easyocr)"
        return True, "ok"

    def version(self) -> str:
        return str(getattr(self._easyocr, "__version__", "unknown"))

    def read_line(self, image: Image.Image) -> str:
        """Recognition-only on the whole image, so the benchmark measures reading, not detection."""
        arr = np.asarray(image.convert("L"))
        h, w = arr.shape
        out = self._reader.recognize(arr, horizontal_list=[[0, w, 0, h]], free_list=[], detail=0)
        return " ".join(str(t).strip() for t in out if str(t).strip())

    def read_document(self, image: Image.Image) -> str:
        arr = np.asarray(image.convert("RGB"))
        results = self._reader.readtext(arr, detail=1, paragraph=False)
        return assemble_rtl([(box, text) for box, text, _conf in results])
