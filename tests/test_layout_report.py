import pandas as pd
import pytest

from urdulens import layout, report


def test_layout_reads_right_to_left_top_to_bottom():
    items = [
        ([[10, 10], [60, 10], [60, 40], [10, 40]], "دو"),  # left piece of line 1
        ([[100, 12], [150, 12], [150, 42], [100, 42]], "ایک"),  # right piece of line 1
        ([[10, 80], [60, 80], [60, 110], [10, 110]], "چار"),
        ([[100, 82], [150, 82], [150, 112], [100, 112]], "تین"),
    ]
    assert layout.assemble_rtl(items) == "ایک دو\nتین چار"


def test_layout_empty_and_blank():
    assert layout.assemble_rtl([]) == ""
    assert layout.assemble_rtl([([0, 10, 0, 10], "  ")]) == ""


def _df():
    return pd.DataFrame(
        {
            "engine": ["a", "a", "b", "b"],
            "sample_id": ["1", "2", "1", "2"],
            "source": ["synthetic"] * 4,
            "style": ["naskh", "nastaliq"] * 2,
            "level": ["clean", "heavy"] * 2,
            "ref": ["abcd", "abcd", "abcd", "abcd"],
            "cer": [0.0, 0.5, 0.25, 0.75],
            "wer": [0.0, 1.0, 0.5, 1.0],
            "cer_strict": [0.0, 0.5, 0.25, 0.75],
            "exact": [True, False, False, False],
            "ms": [10.0, 20.0, 30.0, 40.0],
        }
    )


def test_summarize_ranks_lower_cer_first():
    s = report.summarize(_df())
    assert list(s["engine"]) == ["a", "b"]
    assert s.loc[0, "cer"] == pytest.approx(0.25)
    assert s.loc[0, "exact"] == pytest.approx(0.5)


def test_pivot_orders_levels_easy_to_hard():
    p = report.pivot_cer(_df(), "level")
    assert list(p.columns) == ["clean", "heavy"]


def test_markdown_and_marker_replacement():
    md = report.leaderboard_markdown(_df())
    assert "| Engine |" in md and "25.0%" in md
    text = f"intro\n{report.MARKER_START}\nold\n{report.MARKER_END}\noutro"
    out = report.update_marked_block(text, "NEW")
    assert "NEW" in out and "old" not in out and out.startswith("intro") and out.endswith("outro")
    with pytest.raises(ValueError):
        report.update_marked_block("no markers", "x")
