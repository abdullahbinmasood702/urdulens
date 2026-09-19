"""Character set used for synthetic data and the CRNN model.

Diacritics (zabar, zair, pesh ...) are deliberately excluded: printed everyday
Urdu almost never carries them, and the scoring normaliser strips them anyway.
"""

from __future__ import annotations

# Urdu letters (Unicode code points shown in comments where they are easy to confuse)
URDU_LETTERS = "ءآأؤئابپتٹثجچحخدڈذرڑزژسشصضطظعغفقکگلمنںوہھیے"
#   ک = U+06A9 (keheh, Urdu kaf)   ی = U+06CC (Farsi yeh, Urdu ye)
#   ہ = U+06C1 (heh goal)          ھ = U+06BE (do-chashmi he)
#   ے = U+06D2 (yeh barree)        ں = U+06BA (noon ghunna)

DIGITS_ASCII = "0123456789"
DIGITS_URDU = "۰۱۲۳۴۵۶۷۸۹"  # U+06F0 .. U+06F9 (extended Arabic-Indic, used for Urdu)
PUNCTUATION = " ۔،؟؛!.,:;-()/%٪\"'+=@"
LATIN = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

CHARS = URDU_LETTERS + DIGITS_ASCII + DIGITS_URDU + PUNCTUATION + LATIN
assert len(set(CHARS)) == len(CHARS), "duplicate characters in CHARS"

BLANK = 0  # CTC blank index; real characters start at 1
CHAR2IDX = {c: i + 1 for i, c in enumerate(CHARS)}
IDX2CHAR = {i: c for c, i in CHAR2IDX.items()}
NUM_CLASSES = len(CHARS) + 1


def encode(text: str) -> list[int]:
    """Text -> class indices. Characters outside CHARS are skipped."""
    return [CHAR2IDX[c] for c in text if c in CHAR2IDX]


def decode_indices(indices) -> str:
    """Class indices (no CTC collapsing) -> text."""
    return "".join(IDX2CHAR[i] for i in indices if i in IDX2CHAR)


def unknown_chars(text: str) -> set[str]:
    """Characters in `text` that are not part of CHARS (ignoring newlines)."""
    return {c for c in text if c not in CHAR2IDX and c not in "\n\r\t"}


def ctc_collapse(indices) -> list[int]:
    """Greedy CTC post-processing: merge repeated indices, then drop blanks."""
    out: list[int] = []
    previous = None
    for i in indices:
        i = int(i)
        if i != previous and i != BLANK:
            out.append(i)
        previous = i
    return out
