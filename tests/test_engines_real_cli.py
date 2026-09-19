import pytest

from urdulens import cli, engines, real
from urdulens.engines.base import OCREngine


def test_registry_lists_known_engines_and_rejects_unknown():
    assert {"tesseract", "easyocr", "paddleocr", "urdulens-crnn"} <= set(engines.engine_names())
    with pytest.raises(KeyError):
        engines.create("nope")


def test_custom_engine_registration():
    class Mine(OCREngine):
        def read_line(self, image):
            return "x"

    engines.register("mine", Mine)
    assert engines.create("mine").read_line(None) == "x"


def test_unavailable_engine_gives_reason():
    ok, reason = engines.check("urdulens-crnn")
    if not ok:
        assert reason


def test_tesseract_reads_a_clean_line_when_installed():
    ok, _ = engines.check("tesseract")
    if not ok:
        pytest.skip("Tesseract with Urdu data not installed")
    import numpy as np

    from urdulens import metrics, synth

    img = synth.make_sample(np.random.default_rng(0), "میٹنگ کل صبح گیارہ بجے ہوگی", "lateef", "clean").image
    hyp = engines.create("tesseract").read_line(img)
    assert metrics.cer("میٹنگ کل صبح گیارہ بجے ہوگی", hyp) < 0.5


def test_real_label_validation(tmp_path):
    from PIL import Image

    images = tmp_path / "images"
    images.mkdir()
    Image.new("L", (50, 20), 255).save(images / "a_line01.png")
    Image.new("L", (50, 20), 255).save(images / "b_line01.png")
    labels = tmp_path / "labels.csv"
    labels.write_text(
        "file,text,style,level,group\n"
        "a_line01.png,اردو زبان,nastaliq,photo,a\n"
        "b_line01.png,زَبَر,nastaliq,photo,b\n"  # diacritics -> unsupported characters
        "missing.png,ہے,nastaliq,photo,c\n"
        "a_line01.png,دوبارہ,nastaliq,photo,a\n",
        encoding="utf-8",
    )
    clean, problems = real.validate(labels, images)
    text = "\n".join(problems)
    assert "not found" in text and "outside the supported set" in text and "duplicate" in text
    assert "a_line01.png" in set(clean["file"])


def test_group_split_is_stable_and_groups_never_straddle():
    assert real.split_for_group("bill01") == real.split_for_group("bill01")
    assert {real.split_for_group(f"g{i}") for i in range(200)} == {"train", "val", "test"}


def test_cli_parser_knows_all_commands():
    parser = cli.build_parser()
    for cmd in ["build-benchmark", "preview", "benchmark", "update-readme", "init-db", "prepare-real", "train", "space", "card"]:
        assert parser.parse_args([cmd]).command == cmd


def test_cli_card_and_space(tmp_path):
    assert cli.main(["card", "--out", str(tmp_path / "card.png")]) == 0
    from PIL import Image

    assert Image.open(tmp_path / "card.png").size == (1280, 640)
    assert cli.main(["space", "--out", str(tmp_path / "space")]) == 0
    assert (tmp_path / "space" / "app.py").exists() and (tmp_path / "space" / "urdulens" / "engines" / "base.py").exists()
