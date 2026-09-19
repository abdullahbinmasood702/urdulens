import os

import pandas as pd

from urdulens import corpus, dataset
from urdulens.paths import BENCHMARK_DIR


def test_committed_manifest_is_consistent():
    m = dataset.load_manifest(BENCHMARK_DIR / "synthetic_manifest.csv")
    assert list(m.columns[: len(dataset.MANIFEST_COLUMNS)]) == dataset.MANIFEST_COLUMNS
    assert len(m) == 350 and m["id"].is_unique
    assert all(os.path.exists(p) for p in m["abs_path"])
    assert set(m["split"]) == {"test"} and set(m["source"]) == {"synthetic"}


def test_benchmark_text_never_comes_from_training_sentences():
    m = dataset.load_manifest(BENCHMARK_DIR / "synthetic_manifest.csv")
    sentences = m[m["content_type"] == "sentence"]["text"].unique()
    train = set(corpus.sentences_for("train")) | set(corpus.sentences_for("val"))
    assert not (set(sentences) & train)


def test_build_is_deterministic(tmp_path, monkeypatch):
    monkeypatch.setattr(dataset, "N_SENTENCES", 2)
    monkeypatch.setattr(dataset, "N_NUMERIC", 1)
    a = dataset.build_synthetic_benchmark(tmp_path / "a", tmp_path / "a.csv")
    b = dataset.build_synthetic_benchmark(tmp_path / "b", tmp_path / "b.csv")
    assert a.equals(b)
    assert len(a) == 2 * 5 * 3 + 1 * 5
    import numpy as np
    from PIL import Image

    x = np.asarray(Image.open(tmp_path / "a" / "syn0000.png"))
    y = np.asarray(Image.open(tmp_path / "b" / "syn0000.png"))
    assert np.array_equal(x, y)


def test_load_manifest_rejects_missing_columns(tmp_path):
    p = tmp_path / "bad.csv"
    pd.DataFrame({"id": ["a"]}).to_csv(p, index=False)
    try:
        dataset.load_manifest(p)
    except ValueError as exc:
        assert "missing columns" in str(exc)
    else:
        raise AssertionError("expected ValueError")
