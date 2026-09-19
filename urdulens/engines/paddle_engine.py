"""PaddleOCR engine (Arabic-script model, which also covers Urdu). EXPERIMENTAL.

This wrapper was written against the documented PaddleOCR 2.x and 3.x APIs but
was not run in the environment that produced this repository (model downloads
from Baidu servers were blocked there). Treat the first benchmark run as the
test, and open an issue with the traceback if it fails.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from urdulens.engines.base import OCREngine
from urdulens.layout import assemble_rtl


class PaddleOCREngine(OCREngine):
    name = "paddleocr"
    experimental = True

    def __init__(self, lang: str = "ar"):
        from paddleocr import PaddleOCR

        self._ocr = PaddleOCR(lang=lang)

    @classmethod
    def is_available(cls) -> tuple[bool, str]:
        try:
            import paddleocr  # noqa: F401
        except ImportError:
            return False, "paddleocr is not installed (pip install paddleocr paddlepaddle)"
        return True, "ok"

    def version(self) -> str:
        import paddleocr

        return str(getattr(paddleocr, "__version__", "unknown"))

    def _run(self, image: Image.Image) -> list[tuple[list, str]]:
        arr = np.asarray(image.convert("RGB"))
        if hasattr(self._ocr, "predict"):  # PaddleOCR 3.x
            items = []
            for res in self._ocr.predict(arr):
                data = res if isinstance(res, dict) else getattr(res, "json", {}).get("res", {})
                for poly, text in zip(data.get("rec_polys", []), data.get("rec_texts", [])):
                    items.append((np.asarray(poly).tolist(), text))
            return items
        raw = self._ocr.ocr(arr, cls=False)  # PaddleOCR 2.x
        items = []
        for page in raw or []:
            for box, (text, _conf) in page or []:
                items.append((box, text))
        return items

    def read_line(self, image: Image.Image) -> str:
        return assemble_rtl(self._run(image)).replace("\n", " ")

    def read_document(self, image: Image.Image) -> str:
        return assemble_rtl(self._run(image))
