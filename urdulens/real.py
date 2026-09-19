"""Real-image benchmark data: validate your labels and build the manifest.

Put line images in data/benchmark/real/images/ and a labels.csv next to them:

    file,text,style,level,group
    bill01_line01.png,بجلی کا بل ادا کریں۔,nastaliq,photo,bill01

* style  nastaliq or naskh
* level  photo (taken with a camera) or scan
* group  which page/photo the line came from. Lines from the same group always land
         in the same split, so near-duplicate lines never leak from train to test.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from urdulens import charset, normalize
from urdulens.dataset import MANIFEST_COLUMNS
from urdulens.paths import BENCHMARK_DIR, REAL_BENCH_DIR

REQUIRED = ["file", "text"]
STYLES = {"nastaliq", "naskh"}
LEVELS = {"photo", "scan"}
SPLIT_RATIOS = (0.20, 0.10)  # train, val; the rest (70%) is test


def split_for_group(group: str) -> str:
    x = int(hashlib.sha1(group.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF
    if x < SPLIT_RATIOS[0]:
        return "train"
    if x < SPLIT_RATIOS[0] + SPLIT_RATIOS[1]:
        return "val"
    return "test"


def validate(labels_csv: Path, images_dir: Path) -> tuple[pd.DataFrame, list[str]]:
    """Return (clean dataframe, list of human-readable problems)."""
    problems: list[str] = []
    df = pd.read_csv(labels_csv, encoding="utf-8", dtype=str, keep_default_na=False)
    for col in REQUIRED:
        if col not in df.columns:
            raise ValueError(f"labels.csv needs a '{col}' column")
    for col, default in (("style", "nastaliq"), ("level", "photo"), ("group", "")):
        if col not in df.columns:
            df[col] = default
    keep = []
    for i, row in df.iterrows():
        where = f"row {i + 2} ({row['file']})"
        if not (images_dir / row["file"]).exists():
            problems.append(f"{where}: image file not found")
            continue
        text = normalize.strict(row["text"])
        if not text:
            problems.append(f"{where}: empty text")
            continue
        unknown = charset.unknown_chars(text)
        if unknown:
            shown = " ".join(f"{c!r} (U+{ord(c):04X})" for c in sorted(unknown))
            problems.append(f"{where}: characters outside the supported set: {shown}")
        if row["style"] not in STYLES:
            problems.append(f"{where}: style must be one of {sorted(STYLES)}")
            continue
        if row["level"] not in LEVELS:
            problems.append(f"{where}: level must be one of {sorted(LEVELS)}")
            continue
        keep.append(i)
    clean = df.loc[keep].copy()
    clean["text"] = [normalize.strict(t) for t in clean["text"]]
    dup = clean["file"].duplicated()
    if dup.any():
        problems.append(f"duplicate file names: {sorted(clean.loc[dup, 'file'].unique())}")
        clean = clean[~dup]
    return clean.reset_index(drop=True), problems


def build_manifest(
    labels_csv: Path = REAL_BENCH_DIR / "labels.csv",
    images_dir: Path = REAL_BENCH_DIR / "images",
    out_path: Path = BENCHMARK_DIR / "real_manifest.csv",
) -> tuple[pd.DataFrame, list[str]]:
    clean, problems = validate(labels_csv, images_dir)
    rows = []
    for _, r in clean.iterrows():
        group = r["group"] or Path(r["file"]).stem.split("_line")[0]
        rows.append(
            dict(
                id="real_" + Path(r["file"]).stem,
                path=f"real/images/{r['file']}",
                text=r["text"],
                source="real",
                content_type="sentence",
                style=r["style"],
                font="unknown",
                level=r["level"],
                split=split_for_group(group),
            )
        )
    manifest = pd.DataFrame(rows, columns=MANIFEST_COLUMNS)
    manifest.to_csv(out_path, index=False, encoding="utf-8")
    return manifest, problems
