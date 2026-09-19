"""Text sources and the sentence-level train / val / test split.

Splitting is done per *sentence* with a hash, so the same sentence always lands
in the same split on every machine and the benchmark's test sentences can never
appear in the training data. Extra corpora (for example text fetched from
Urdu Wikipedia) are picked up automatically from data/corpus/extra/*.txt, and
are split the same way.
"""

from __future__ import annotations

import hashlib
import unicodedata
from functools import lru_cache

import numpy as np

from urdulens import charset
from urdulens.paths import CORPUS_DIR

SPLITS = ("train", "val", "test")
SPLIT_RATIOS = (0.70, 0.10, 0.20)


def _clean(line: str) -> str:
    return unicodedata.normalize("NFC", line.strip())


def split_of(sentence: str) -> str:
    """Deterministic split assignment from the sentence text alone."""
    digest = hashlib.sha1(_clean(sentence).encode("utf-8")).hexdigest()
    x = int(digest[:8], 16) / 0xFFFFFFFF
    if x < SPLIT_RATIOS[0]:
        return "train"
    if x < SPLIT_RATIOS[0] + SPLIT_RATIOS[1]:
        return "val"
    return "test"


@lru_cache(maxsize=1)
def load_sentences() -> tuple[str, ...]:
    """All sentences from the bundled corpus plus any extra corpora, de-duplicated."""
    files = [CORPUS_DIR / "sentences_ur.txt"]
    extra = CORPUS_DIR / "extra"
    if extra.is_dir():
        files += sorted(extra.glob("*.txt"))
    seen: dict[str, None] = {}
    for path in files:
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = _clean(raw)
            if not line or line.startswith("#"):
                continue
            if charset.unknown_chars(line):  # skip lines the model could not be trained on
                continue
            seen.setdefault(line, None)
    return tuple(seen)


def sentences_for(split: str) -> list[str]:
    if split not in SPLITS:
        raise ValueError(f"split must be one of {SPLITS}, got {split!r}")
    return [s for s in load_sentences() if split_of(s) == split]


def vocabulary(split: str = "train") -> list[str]:
    """Distinct words from one split (used to build word-shuffled training lines)."""
    words: dict[str, None] = {}
    for sentence in sentences_for(split):
        for word in sentence.split():
            words.setdefault(word, None)
    return list(words)


_URDU_DIGITS = charset.DIGITS_URDU
_ASCII_DIGITS = charset.DIGITS_ASCII


def random_number_line(rng: np.random.Generator) -> str:
    """A short line of numbers, dates, prices or phone-like digits (both digit styles)."""
    digits = _URDU_DIGITS if rng.random() < 0.5 else _ASCII_DIGITS

    def num(n: int) -> str:
        return "".join(rng.choice(list(digits), size=n))

    kind = int(rng.integers(0, 5))
    if kind == 0:  # amount
        return f"{num(int(rng.integers(2, 6)))} روپے"
    if kind == 1:  # date
        return f"{num(2)}/{num(2)}/{'20' if digits == _ASCII_DIGITS else '۲۰'}{num(2)}"
    if kind == 2:  # phone-like
        return f"{num(4)} {num(7)}"
    if kind == 3:  # reference number
        return f"نمبر {num(int(rng.integers(3, 9)))}"
    return f"{num(int(rng.integers(1, 3)))} بجے سے {num(int(rng.integers(1, 3)))} بجے تک"


def random_line(rng: np.random.Generator, split: str = "train") -> str:
    """Training text: real sentences, word shuffles and number lines, mixed."""
    pool = sentences_for(split)
    vocab = vocabulary(split)
    r = rng.random()
    if r < 0.50 and pool:
        return pool[int(rng.integers(0, len(pool)))]
    if r < 0.85 and vocab:
        n = int(rng.integers(3, 9))
        return " ".join(vocab[int(i)] for i in rng.integers(0, len(vocab), size=n)) + (
            "۔" if rng.random() < 0.5 else ""
        )
    return random_number_line(rng)
