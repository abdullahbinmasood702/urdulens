"""Engine registry. Add your own with `register("name", YourEngine)`.

Engines are imported lazily: importing this package never imports torch,
easyocr or paddle, so the dashboard and tests stay light.
"""

from __future__ import annotations

from urdulens.engines.base import OCREngine

_REGISTRY: dict[str, str] = {
    "tesseract": "urdulens.engines.tesseract:TesseractEngine",
    "easyocr": "urdulens.engines.easyocr_engine:EasyOCREngine",
    "paddleocr": "urdulens.engines.paddle_engine:PaddleOCREngine",
    "urdulens-crnn": "urdulens.engines.crnn_engine:CRNNEngine",
}
_CUSTOM: dict[str, type[OCREngine]] = {}

DEFAULT_ENGINES = ("tesseract", "easyocr", "urdulens-crnn")


def register(name: str, cls: type[OCREngine]) -> None:
    _CUSTOM[name] = cls


def engine_names() -> list[str]:
    return sorted(set(_REGISTRY) | set(_CUSTOM))


def _resolve(name: str) -> type[OCREngine]:
    if name in _CUSTOM:
        return _CUSTOM[name]
    if name not in _REGISTRY:
        raise KeyError(f"Unknown engine {name!r}. Known: {engine_names()}")
    module_path, cls_name = _REGISTRY[name].split(":")
    import importlib

    return getattr(importlib.import_module(module_path), cls_name)


def check(name: str) -> tuple[bool, str]:
    """Is this engine usable right now? (available, reason)"""
    return _resolve(name).is_available()


def create(name: str, **kwargs) -> OCREngine:
    cls = _resolve(name)
    ok, reason = cls.is_available()
    if not ok:
        raise RuntimeError(f"Engine {name!r} unavailable: {reason}")
    engine = cls(**kwargs)
    engine.name = name
    return engine
