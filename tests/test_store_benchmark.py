import pandas as pd
from PIL import Image

from urdulens import benchmark, engines, store
from urdulens.engines.base import OCREngine


class PerfectEngine(OCREngine):
    """Cheats by reading the answer from a lookup keyed on image size."""

    name = "perfect"

    def __init__(self, answers):
        self.answers = answers

    def read_line(self, image: Image.Image) -> str:
        return self.answers[image.size]


class BlankEngine(OCREngine):
    name = "blank"

    def read_line(self, image):
        return ""


class BrokenEngine(OCREngine):
    name = "broken"

    def read_line(self, image):
        raise RuntimeError("boom")


def _manifest(tmp_path, n=3):
    rows = []
    answers = {}
    for i in range(n):
        size = (40 + i, 20)
        Image.new("L", size, 255).save(tmp_path / f"{i}.png")
        text = "اردو" + "ا" * i
        answers[size] = text
        rows.append(
            dict(id=f"s{i}", path=f"{i}.png", text=text, source="synthetic", content_type="sentence",
                 style="naskh", font="lateef", level="clean", split="test", abs_path=str(tmp_path / f"{i}.png"))
        )
    return pd.DataFrame(rows), answers


def test_perfect_blank_and_broken_engines(tmp_path):
    m, answers = _manifest(tmp_path)
    perfect = benchmark.run_engine(PerfectEngine(answers), m)
    assert all(r["cer"] == 0 and r["exact"] for r in perfect)
    blank = benchmark.run_engine(BlankEngine(), m)
    assert all(r["cer"] == 1.0 for r in blank)
    broken = benchmark.run_engine(BrokenEngine(), m)  # must not raise
    assert all(r["hyp"] == "" for r in broken)


def test_run_benchmark_skips_unavailable_engines(tmp_path):
    engines.register("blank", BlankEngine)
    m, _ = _manifest(tmp_path)
    rows, skipped = benchmark.run_benchmark(["blank", "paddleocr"], m, log=lambda *_: None)
    assert {r["engine"] for r in rows} == {"blank"}
    assert "paddleocr" in skipped or any(r["engine"] == "paddleocr" for r in rows)


def test_store_round_trip(sqlite_url, tmp_path):
    m, answers = _manifest(tmp_path)
    rows = benchmark.run_engine(PerfectEngine(answers), m)
    eng = store.init_db()
    run_id = store.save_run(eng, "synthetic", rows, git_sha="abc", notes="t")
    assert run_id == 1
    assert len(store.load_results(eng)) == len(rows)
    assert store.load_runs(eng).loc[0, "n_samples"] == len(m)
    assert store.load_results(eng, run_id=999).empty


def test_database_url_prefers_env_and_fixes_postgres_scheme(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h/db")
    assert store.database_url() == "postgresql://u:p@h/db"
    monkeypatch.delenv("DATABASE_URL")
    assert store.database_url().startswith("sqlite:///")
