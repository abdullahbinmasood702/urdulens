"""Common interface every OCR engine implements."""

from __future__ import annotations

from abc import ABC, abstractmethod

from PIL import Image


class OCREngine(ABC):
    """An OCR engine that reads Urdu text from an image.

    Engines are compared on *line images* (one line of text per image), so
    `read_line` is what the benchmark calls. `read_document` is what the reader
    app calls for a whole photo or page; it defaults to `read_line`.
    """

    name: str = "engine"
    experimental: bool = False

    @classmethod
    def is_available(cls) -> tuple[bool, str]:
        """(available, reason). The reason explains what is missing when unavailable."""
        return True, "ok"

    def version(self) -> str:
        return "unknown"

    @abstractmethod
    def read_line(self, image: Image.Image) -> str:
        """Return the text in a single-line image, in logical (typing) order."""

    def read_document(self, image: Image.Image) -> str:
        return self.read_line(image)
