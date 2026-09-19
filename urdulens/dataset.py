"""Benchmark datasets: building the frozen synthetic set and loading manifests.

A manifest is a CSV with one row per line image:

    id, path, text, source, content_type, style, font, level, split

* source        "synthetic" or "real"
* content_type  "sentence" or "numeric"
* style         "nastaliq" or "naskh" (real images: whatever the labeler chose)
* level         clean / mild / heavy for synthetic images, "photo" or "scan" for real ones
* split         "test" for benchmark rows (train/val rows exist only for real data
                that is used to fine-tune a model)
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

from urdulens import augment, corpus, fonts, synth
from urdulens.paths import BENCHMARK_DIR, SYNTH_BENCH_DIR

MANIFEST_COLUMNS = ["id", "path", "text", "source", "content_type", "style", "font", "level", "split"]
BENCH_SEED = 2026
N_SENTENCES = 20  # held-out test sentences used per font x level
N_NUMERIC = 10  # numeric lines per font (mild level only)


def _stable_order(sentences: list[str]) -> list[str]:
    """Order sentences by hash so the chosen subset does not depend on file order."""
    return sorted(sentences, key=lambda s: hashlib.sha1(s.encode("utf-8")).hexdigest())


def build_synthetic_benchmark(
    out_dir: Path = SYNTH_BENCH_DIR,
    manifest_path: Path | None = None,
    seed: int = BENCH_SEED,
) -> pd.DataFrame:
    """Render the frozen synthetic benchmark to `out_dir` and write its manifest.

    Text comes only from the *test* split of the corpus, so no training sentence
    can appear here. Each row gets its own RNG stream: adding fonts later does
    not change the images of existing rows.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(manifest_path or BENCHMARK_DIR / "synthetic_manifest.csv")
    available = fonts.available_fonts()
    if not available:
        raise FileNotFoundError("No fonts found in fonts/. See fonts/README.md.")

    sentences = _stable_order(corpus.sentences_for("test"))[:N_SENTENCES]
    if len(sentences) < N_SENTENCES:
        raise RuntimeError(f"Need {N_SENTENCES} test sentences, corpus only has {len(sentences)}.")

    number_rng = np.random.default_rng([seed, 999])
    numeric_lines = [corpus.random_number_line(number_rng) for _ in range(N_NUMERIC)]

    rows: list[dict] = []
    jobs: list[tuple[str, str, str, str]] = []  # (text, content_type, font, level)
    for text in sentences:
        for key in available:
            for level in augment.LEVELS:
                jobs.append((text, "sentence", key, level))
    for text in numeric_lines:
        for key in available:
            jobs.append((text, "numeric", key, "mild"))

    for idx, (text, ctype, key, level) in enumerate(jobs):
        rng = np.random.default_rng([seed, idx])
        sample = synth.make_sample(rng, text, key, level)
        sid = f"syn{idx:04d}"
        rel = f"synthetic/{sid}.png"
        sample.image.save(out_dir / f"{sid}.png", optimize=True)
        rows.append(
            dict(
                id=sid,
                path=rel,
                text=text,
                source="synthetic",
                content_type=ctype,
                style=sample.style,
                font=key,
                level=level,
                split="test",
            )
        )
    df = pd.DataFrame(rows, columns=MANIFEST_COLUMNS)
    df.to_csv(manifest_path, index=False, encoding="utf-8")
    return df


def load_manifest(path: Path | str, base_dir: Path | None = None) -> pd.DataFrame:
    """Read a manifest and add an absolute `abs_path` column."""
    path = Path(path)
    df = pd.read_csv(path, encoding="utf-8", dtype=str, keep_default_na=False)
    missing = [c for c in MANIFEST_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing columns: {missing}")
    base = Path(base_dir) if base_dir else path.parent
    df["abs_path"] = [str(base / p) for p in df["path"]]
    return df


def load_benchmark(which: str = "all", split: str = "test") -> pd.DataFrame:
    """Load the synthetic and/or real benchmark manifests (test split by default)."""
    frames = []
    if which in ("all", "synthetic"):
        p = BENCHMARK_DIR / "synthetic_manifest.csv"
        if p.exists():
            frames.append(load_manifest(p))
    if which in ("all", "real"):
        p = BENCHMARK_DIR / "real_manifest.csv"
        if p.exists():
            frames.append(load_manifest(p))
    if not frames:
        raise FileNotFoundError(
            "No benchmark manifest found. Run `urdulens build-benchmark` (synthetic) "
            "or `urdulens prepare-real` (real images)."
        )
    df = pd.concat(frames, ignore_index=True)
    return df[df["split"] == split].reset_index(drop=True)


def iter_images(df: pd.DataFrame) -> Iterator[tuple[pd.Series, Image.Image]]:
    for _, row in df.iterrows():
        with Image.open(row["abs_path"]) as im:
            yield row, im.convert("L")
