"""Filesystem locations. The repo root is found relative to this file."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = Path(os.environ.get("URDULENS_FONT_DIR", ROOT / "fonts"))
CORPUS_DIR = ROOT / "data" / "corpus"
BENCHMARK_DIR = ROOT / "data" / "benchmark"
SYNTH_BENCH_DIR = BENCHMARK_DIR / "synthetic"
REAL_BENCH_DIR = BENCHMARK_DIR / "real"
RESULTS_DIR = ROOT / "results"
MODEL_DIR = ROOT / "models"
DEFAULT_MODEL = Path(os.environ.get("URDULENS_MODEL", MODEL_DIR / "urdulens_crnn.pt"))
