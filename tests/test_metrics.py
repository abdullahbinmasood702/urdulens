import pytest

from urdulens import metrics


def test_identical_is_zero():
    s = metrics.score_pair("میں آج", "میں آج")
    assert s.cer == 0 and s.wer == 0 and s.exact


def test_known_distances():
    assert metrics.edit_distance("abc", "abd") == 1
    assert metrics.edit_distance(["a", "b"], ["a"]) == 1
    s = metrics.score_pair("میں آج", "مین اج")
    assert s.char_errors == 2 and s.char_total == 6
    assert s.cer == pytest.approx(2 / 6)
    assert s.wer == pytest.approx(1.0)


def test_empty_reference():
    assert metrics.cer("", "") == 0.0
    assert metrics.cer("", "x") == 1.0


def test_script_variants_not_penalised_in_headline_but_visible_in_strict():
    s = metrics.score_pair("کیف", "كيف")  # Urdu vs Arabic letter shapes
    assert s.cer == 0
    assert s.cer_strict > 0


def test_cer_can_exceed_one():
    assert metrics.cer("اب", "ابجدہوز") > 1
