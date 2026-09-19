"""Text normalisation used before scoring OCR output.

Two levels are provided so a leaderboard can report both:

* ``strict``     - Unicode NFKC, invisible characters removed, spaces collapsed.
* ``normalized`` - strict + Arabic/Urdu look-alike letters unified, diacritics and
                   tatweel removed, digits mapped to ASCII, punctuation unified.

The second level answers "did the engine read the right *letters*?" without
punishing it for emitting an Arabic yeh (U+064A) where a Farsi yeh (U+06CC) was
typeset, which is a keyboard/encoding habit and not a reading error.
"""

from __future__ import annotations

import re
import unicodedata

# Look-alike letters -> the code point Urdu keyboards use
_LETTER_MAP = {
    "\u064a": "\u06cc",  # Arabic yeh        -> Farsi yeh (Urdu ye)
    "\u0649": "\u06cc",  # alef maksura      -> Farsi yeh
    "\u0643": "\u06a9",  # Arabic kaf        -> keheh (Urdu kaf)
    "\u0647": "\u06c1",  # Arabic heh        -> heh goal
    "\u06d5": "\u06c1",  # ae (Kurdish/Uyghur) -> heh goal
}

_PUNCT_MAP = {
    "\u06d4": ".",  # Urdu full stop
    "\u060c": ",",  # Arabic comma
    "\u061f": "?",  # Arabic question mark
    "\u061b": ";",  # Arabic semicolon
    "\u066a": "%",  # Arabic percent sign
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
}

# Arabic-Indic (U+0660..0669) and extended Arabic-Indic (U+06F0..06F9) -> ASCII
_DIGIT_MAP = {chr(0x0660 + i): str(i) for i in range(10)}
_DIGIT_MAP.update({chr(0x06F0 + i): str(i) for i in range(10)})

# Invisible formatting characters: ZWSP, ZWNJ, ZWJ, LRM, RLM, bidi controls, BOM
_INVISIBLE = re.compile("[\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]")
# Harakat, Quranic marks and dagger alef, plus tatweel
_DIACRITICS = re.compile("[\u064b-\u065f\u0670\u06d6-\u06ed\u0640]")
_SPACES = re.compile(r"\s+")


def strict(text: str) -> str:
    """NFKC, drop invisible characters, collapse whitespace."""
    text = unicodedata.normalize("NFKC", text or "")
    text = _INVISIBLE.sub("", text)
    return _SPACES.sub(" ", text).strip()


def normalized(text: str) -> str:
    """Script-variant-insensitive form used for the headline CER/WER."""
    text = strict(text)
    text = _DIACRITICS.sub("", text)
    text = "".join(_LETTER_MAP.get(c, c) for c in text)
    text = "".join(_DIGIT_MAP.get(c, c) for c in text)
    text = "".join(_PUNCT_MAP.get(c, c) for c in text)
    return _SPACES.sub(" ", text).strip()
