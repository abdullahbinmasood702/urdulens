"""Logical <-> visual order conversion for right-to-left text.

Urdu strings are stored in *logical* (typing) order. A line-recognition model
that scans an image from left to right sees characters in *visual* order, so
labels are converted with the Unicode bidirectional algorithm for training and
converted back after decoding. Numbers and Latin words inside an Urdu sentence
are why a plain string reversal is not enough.
"""

from __future__ import annotations

try:  # python-bidi >= 0.5
    from bidi import get_display as _get_display
except ImportError:  # pragma: no cover - older python-bidi
    from bidi.algorithm import get_display as _get_display


def to_visual(text: str) -> str:
    """Logical order -> left-to-right visual order (paragraph direction RTL)."""
    if not text:
        return text
    return _get_display(text, base_dir="R")


def to_logical(visual: str) -> str:
    """Left-to-right visual order -> logical order (inverse of `to_visual`)."""
    if not visual:
        return visual
    return _get_display(visual, base_dir="R")
