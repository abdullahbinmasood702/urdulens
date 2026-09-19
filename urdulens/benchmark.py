"""Run OCR engines over a manifest and score them."""

from __future__ import annotations

import subprocess
import time
from collections.abc import Callable

import pandas as pd

from urdulens import dataset, engines, metrics


def git_sha() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5, check=True
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def run_engine(
    engine,
    manifest: pd.DataFrame,
    progress: Callable[[int, int], None] | None = None,
) -> list[dict]:
    """Read every image in `manifest` with `engine`; return per-sample result rows."""
    rows: list[dict] = []
    total = len(manifest)
    for i, (row, image) in enumerate(dataset.iter_images(manifest), start=1):
        t0 = time.perf_counter()
        try:
            hyp = engine.read_line(image)
        except Exception as exc:  # one bad image must not abort a whole run
            hyp = ""
            print(f"  [{engine.name}] failed on {row['id']}: {exc}")
        ms = (time.perf_counter() - t0) * 1000
        score = metrics.score_pair(row["text"], hyp)
        rows.append(
            dict(
                engine=engine.name,
                engine_version=engine.version(),
                sample_id=row["id"],
                source=row["source"],
                content_type=row["content_type"],
                style=row["style"],
                font=row["font"],
                level=row["level"],
                ref=row["text"],
                hyp=hyp,
                cer=score.cer,
                wer=score.wer,
                cer_strict=score.cer_strict,
                exact=score.exact,
                ms=ms,
            )
        )
        if progress:
            progress(i, total)
    return rows


def run_benchmark(
    engine_names: list[str],
    manifest: pd.DataFrame,
    log=print,
) -> tuple[list[dict], dict[str, str]]:
    """Run several engines. Returns (all result rows, {engine: skip reason})."""
    all_rows: list[dict] = []
    skipped: dict[str, str] = {}
    for name in engine_names:
        ok, reason = engines.check(name)
        if not ok:
            skipped[name] = reason
            log(f"Skipping {name}: {reason}")
            continue
        log(f"Running {name} on {len(manifest)} lines ...")
        engine = engines.create(name)

        def tick(i: int, n: int, _name=name) -> None:
            if i % 50 == 0 or i == n:
                log(f"  {_name}: {i}/{n}")

        all_rows.extend(run_engine(engine, manifest, tick))
    return all_rows, skipped
