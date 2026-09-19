"""The UrduLens CRNN (trained on synthetic data with train/crnn.py)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from urdulens.engines.base import OCREngine
from urdulens.paths import DEFAULT_MODEL


class CRNNEngine(OCREngine):
    name = "urdulens-crnn"

    def __init__(self, checkpoint: Path | str | None = None, device: str = "cpu"):
        from urdulens import model as m

        self._m = m
        self._net, self._meta = m.load_checkpoint(checkpoint or DEFAULT_MODEL, device)
        self._device = device

    @classmethod
    def is_available(cls) -> tuple[bool, str]:
        try:
            import torch  # noqa: F401
        except ImportError:
            return False, "torch is not installed"
        if not Path(DEFAULT_MODEL).exists():
            return False, f"no trained model at {DEFAULT_MODEL} (see docs/TRAINING.md)"
        return True, "ok"

    def version(self) -> str:
        return str(self._meta.get("version", "unknown"))

    def read_line(self, image: Image.Image) -> str:
        return self._m.predict_line(self._net, image, self._device)
