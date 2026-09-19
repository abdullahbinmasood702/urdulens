# Adding an OCR engine

An engine is any object that turns a line image into text. Three steps.

## 1. Write the wrapper

```python
# urdulens/engines/my_engine.py
from PIL import Image
from urdulens.engines.base import OCREngine


class MyEngine(OCREngine):
    name = "my-engine"

    def __init__(self):
        import my_ocr_library            # import heavy libraries here, not at module top
        self._ocr = my_ocr_library.load("ur")

    @classmethod
    def is_available(cls) -> tuple[bool, str]:
        try:
            import my_ocr_library         # noqa: F401
        except ImportError:
            return False, "my_ocr_library is not installed (pip install my-ocr-library)"
        return True, "ok"

    def version(self) -> str:
        return "1.2.3"                    # stored with every result

    def read_line(self, image: Image.Image) -> str:
        return self._ocr.read(image)      # logical (typing) order, Urdu Unicode
```

Rules that keep the benchmark fair:

* `read_line` receives **one line**. Do not add detection or layout steps unless the engine cannot work without them.
* Return text in **logical order**. If your engine returns visual order, convert with `urdulens.textorder.to_logical`.
* No tuning on the benchmark images.

For whole-page reading also override `read_document` (see `easyocr_engine.py`; `urdulens.layout.assemble_rtl` sorts boxes
into Urdu reading order).

## 2. Register it

In `urdulens/engines/__init__.py` add one line to `_REGISTRY`:

```python
"my-engine": "urdulens.engines.my_engine:MyEngine",
```

## 3. Run it

```powershell
urdulens benchmark --engines tesseract,my-engine
```

Add it to `DEFAULT_ENGINES` and the workflow's `--engines` list once it works on a free GitHub runner (CPU only, under
about an hour). Big models (for example vision-language models) are welcome as engines but may need a GPU, so run
them locally and share the resulting numbers in an issue.
