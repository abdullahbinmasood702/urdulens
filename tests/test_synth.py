import numpy as np
import pytest

from urdulens import augment, fonts, synth


def test_all_bundled_fonts_present():
    assert set(fonts.available_fonts()) == set(fonts.FONT_KEYS)


@pytest.mark.parametrize("key", fonts.FONT_KEYS)
def test_render_produces_ink(key):
    img = synth.render_line("اردو زبان", key, 40)
    arr = np.asarray(img)
    assert img.mode == "L" and arr.min() < 100 and arr.max() > 200


def test_same_seed_same_image():
    a = synth.make_sample(np.random.default_rng(5), "بازار بند ہے", "gulzar", "heavy").image
    b = synth.make_sample(np.random.default_rng(5), "بازار بند ہے", "gulzar", "heavy").image
    assert np.array_equal(np.asarray(a), np.asarray(b))


@pytest.mark.parametrize("level", augment.LEVELS)
def test_levels_run(level):
    s = synth.make_sample(np.random.default_rng(1), "پانی پیجیے", level=level)
    assert s.level == level and s.image.width > 20


def test_heavy_differs_from_clean():
    rng = np.random.default_rng(2)
    base = synth.render_line("آج موسم صاف ہے", "lateef", 50)
    clean = np.asarray(augment.degrade(base, "clean", rng), dtype=float)
    heavy = np.asarray(augment.degrade(base, "heavy", rng), dtype=float)
    assert clean.shape != heavy.shape or np.abs(clean - heavy).mean() > 2


def test_unknown_level_rejected():
    with pytest.raises(ValueError):
        augment.degrade(synth.render_line("ا", "lateef", 40), "extreme", np.random.default_rng(0))
