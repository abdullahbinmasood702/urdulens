"""Character and word error rates for OCR output."""

from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz.distance import Levenshtein

from urdulens import normalize


def edit_distance(a, b) -> int:
    """Levenshtein distance between two strings or two token lists."""
    return int(Levenshtein.distance(a, b))


@dataclass(frozen=True)
class PairScore:
    """Error counts for one (reference, hypothesis) pair, normalized form."""

    char_errors: int
    char_total: int
    word_errors: int
    word_total: int
    strict_char_errors: int
    strict_char_total: int
    exact: bool

    @property
    def cer(self) -> float:
        return _rate(self.char_errors, self.char_total, self.char_errors)

    @property
    def wer(self) -> float:
        return _rate(self.word_errors, self.word_total, self.word_errors)

    @property
    def cer_strict(self) -> float:
        return _rate(self.strict_char_errors, self.strict_char_total, self.strict_char_errors)


def _rate(errors: int, total: int, fallback_errors: int) -> float:
    """errors / total; if the reference is empty, 0.0 when nothing was output else 1.0."""
    if total == 0:
        return 0.0 if fallback_errors == 0 else 1.0
    return errors / total


def score_pair(reference: str, hypothesis: str) -> PairScore:
    ref_n, hyp_n = normalize.normalized(reference), normalize.normalized(hypothesis)
    ref_s, hyp_s = normalize.strict(reference), normalize.strict(hypothesis)
    ref_words, hyp_words = ref_n.split(), hyp_n.split()
    return PairScore(
        char_errors=edit_distance(ref_n, hyp_n),
        char_total=len(ref_n),
        word_errors=edit_distance(ref_words, hyp_words),
        word_total=len(ref_words),
        strict_char_errors=edit_distance(ref_s, hyp_s),
        strict_char_total=len(ref_s),
        exact=ref_n == hyp_n,
    )


def cer(reference: str, hypothesis: str) -> float:
    return score_pair(reference, hypothesis).cer


def wer(reference: str, hypothesis: str) -> float:
    return score_pair(reference, hypothesis).wer
