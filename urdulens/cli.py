"""Command line interface:  urdulens <command>  (or  python -m urdulens <command>)."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from urdulens import __version__
from urdulens.paths import BENCHMARK_DIR, RESULTS_DIR, ROOT


def cmd_build_benchmark(args) -> int:
    from urdulens import dataset

    df = dataset.build_synthetic_benchmark()
    print(f"Wrote {len(df)} images and data/benchmark/synthetic_manifest.csv")
    print(df.groupby(["content_type", "style"]).size().to_string())
    return 0


def cmd_preview(args) -> int:
    import numpy as np
    from PIL import Image

    from urdulens import corpus, fonts, synth

    rng = np.random.default_rng(7)
    sentences = corpus.sentences_for("test")[:3]
    rows = []
    for text in sentences:
        for level in ("clean", "mild", "heavy"):
            key = fonts.available_fonts()[len(rows) % len(fonts.available_fonts())]
            rows.append(synth.make_sample(rng, text, key, level))
    width = max(s.image.width for s in rows)
    height = sum(s.image.height + 8 for s in rows)
    sheet = Image.new("L", (width, height), 255)
    y = 0
    for s in rows:
        sheet.paste(s.image, (0, y))
        y += s.image.height + 8
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, optimize=True)
    print(f"Saved {out}")
    return 0


def cmd_benchmark(args) -> int:
    from urdulens import benchmark, dataset, engines, report, store

    manifest = dataset.load_benchmark(args.dataset)
    present = manifest["abs_path"].map(os.path.exists)
    if not present.all():
        print(f"Warning: {int((~present).sum())} listed image files are missing and will be skipped.")
        manifest = manifest[present].reset_index(drop=True)
    if args.limit:
        manifest = manifest.sample(n=min(args.limit, len(manifest)), random_state=0).reset_index(drop=True)
    names = [n.strip() for n in args.engines.split(",") if n.strip()] if args.engines else list(engines.DEFAULT_ENGINES)
    rows, skipped = benchmark.run_benchmark(names, manifest)
    if not rows:
        print("No engine ran. Install at least one (see docs/GUIDE.md) and try again.")
        return 1

    import pandas as pd

    df = pd.DataFrame(rows)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    md = report.leaderboard_markdown(df, title=f"{len(manifest)} lines, dataset: {args.dataset}")
    (RESULTS_DIR / "leaderboard.md").write_text(md + "\n", encoding="utf-8")
    df.drop(columns=["ref", "hyp"]).to_csv(RESULTS_DIR / "latest_scores.csv", index=False)
    (RESULTS_DIR / "latest.json").write_text(
        json.dumps(
            {
                "dataset": args.dataset,
                "lines": len(manifest),
                "engines": sorted(df["engine"].unique()),
                "skipped": skipped,
                "summary": report.summarize(df).round(4).to_dict(orient="records"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("\n" + md)
    if not args.no_store:
        engine = store.init_db()
        run_id = store.save_run(engine, args.dataset, rows, git_sha=benchmark.git_sha(), notes=args.notes)
        print(f"\nStored run #{run_id} in {engine.url.render_as_string(hide_password=True)}")
    return 0


def cmd_update_readme(args) -> int:
    from urdulens import report

    readme = ROOT / "README.md"
    block = (RESULTS_DIR / "leaderboard.md").read_text(encoding="utf-8").strip()
    readme.write_text(report.update_marked_block(readme.read_text(encoding="utf-8"), block), encoding="utf-8")
    print("README leaderboard updated.")
    return 0


def cmd_init_db(args) -> int:
    from urdulens import store

    engine = store.init_db()
    print("Tables ready in", engine.url.render_as_string(hide_password=True))
    return 0


def cmd_prepare_real(args) -> int:
    from urdulens import real

    manifest, problems = real.build_manifest()
    for p in problems:
        print("PROBLEM:", p)
    counts = manifest["split"].value_counts().to_dict()
    print(f"Manifest written: {len(manifest)} lines, splits: {counts}")
    return 1 if problems else 0


def cmd_train(args) -> int:
    from urdulens import train

    train.train(
        steps=args.steps,
        batch_size=args.batch_size,
        lr=args.lr,
        device=args.device,
        out=args.out,
        workers=args.workers,
        real_manifest=BENCHMARK_DIR / "real_manifest.csv" if args.use_real else None,
        wandb_project=args.wandb_project,
    )
    return 0


def cmd_space(args) -> int:
    """Assemble a ready-to-upload Hugging Face Space folder for the Reader app."""
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    (out / "urdulens").mkdir(parents=True)
    for src in (ROOT / "urdulens").glob("*.py"):
        shutil.copy(src, out / "urdulens" / src.name)
    shutil.copytree(ROOT / "urdulens" / "engines", out / "urdulens" / "engines", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy(ROOT / "apps" / "reader.py", out / "app.py")
    shutil.copy(ROOT / "apps" / "_common.py", out / "_common.py")
    for name in ("README.md", "requirements.txt", "packages.txt"):
        shutil.copy(ROOT / "deploy" / "hf-space" / name, out / name)
    print(f"Space folder ready: {out}  (upload its contents to a new Hugging Face Space)")
    return 0


def cmd_card(args) -> int:
    from urdulens import card

    out = card.make_card(
        title="UrduLens",
        subtitle="Open benchmark that measures how well OCR engines read Urdu.",
        name="ABDULLAH BIN MASOOD",
        org="Code with ABM",
        pills=["Python", "OCR", "PostgreSQL", "GitHub Actions", "Streamlit"],
        logo=ROOT / "assets" / "logo.png",
        out=Path(args.out),
    )
    print("Saved", out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="urdulens", description="Urdu OCR benchmark and toolkit")
    p.add_argument("--version", action="version", version=f"urdulens {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("build-benchmark", help="regenerate the frozen synthetic benchmark").set_defaults(func=cmd_build_benchmark)

    s = sub.add_parser("preview", help="save a contact sheet of synthetic samples")
    s.add_argument("--out", default=str(ROOT / "assets" / "synthetic_samples.png"))
    s.set_defaults(func=cmd_preview)

    s = sub.add_parser("benchmark", help="run OCR engines on the benchmark")
    s.add_argument("--engines", default="", help="comma list, e.g. tesseract,easyocr (default: all that are installed)")
    s.add_argument("--dataset", default="all", choices=["all", "synthetic", "real"])
    s.add_argument("--limit", type=int, default=0, help="score a random subset (quick test)")
    s.add_argument("--no-store", action="store_true", help="do not write to the database")
    s.add_argument("--notes", default=None)
    s.set_defaults(func=cmd_benchmark)

    sub.add_parser("update-readme", help="paste results/leaderboard.md into the README").set_defaults(func=cmd_update_readme)
    sub.add_parser("init-db", help="create database tables (SQLite, or Neon if DATABASE_URL is set)").set_defaults(func=cmd_init_db)
    sub.add_parser("prepare-real", help="validate real labels and build the real manifest").set_defaults(func=cmd_prepare_real)

    s = sub.add_parser("train", help="train the CRNN model (use a GPU)")
    s.add_argument("--steps", type=int, default=20000)
    s.add_argument("--batch-size", type=int, default=32)
    s.add_argument("--lr", type=float, default=1e-3)
    s.add_argument("--device", default="auto")
    s.add_argument("--workers", type=int, default=2)
    s.add_argument("--out", default=None)
    s.add_argument("--use-real", action="store_true", help="mix in your real training lines")
    s.add_argument("--wandb-project", default=None)
    s.set_defaults(func=cmd_train)

    s = sub.add_parser("space", help="build a Hugging Face Space folder for the Reader app")
    s.add_argument("--out", default=str(ROOT / "dist" / "hf-space"))
    s.set_defaults(func=cmd_space)

    s = sub.add_parser("card", help="make the 1280x640 social preview image")
    s.add_argument("--out", default=str(ROOT / "assets" / "social-card.png"))
    s.set_defaults(func=cmd_card)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if getattr(args, "out", "unset") is None and args.command == "train":
        from urdulens.paths import DEFAULT_MODEL

        args.out = str(DEFAULT_MODEL)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
