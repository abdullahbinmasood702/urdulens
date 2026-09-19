"""Turn per-sample results into leaderboards (pandas + plain markdown, no extra deps)."""

from __future__ import annotations

import pandas as pd

MARKER_START = "<!-- LEADERBOARD:START -->"
MARKER_END = "<!-- LEADERBOARD:END -->"

# Natural left-to-right order for breakdown tables (easy to hard).
COLUMN_ORDER = {
    "level": ["clean", "mild", "heavy", "scan", "photo"],
    "style": ["nastaliq", "naskh"],
    "content_type": ["sentence", "numeric"],
    "source": ["synthetic", "real"],
}


def summarize(df: pd.DataFrame, by: list[str] | None = None) -> pd.DataFrame:
    """Aggregate per-sample rows into one row per engine (and optional groups).

    CER/WER are computed per sample and averaged with equal weight (macro), and
    also reported as micro-averages for CER via the reference length when the
    `ref` column is present. Lower is better.
    """
    if df.empty:
        return pd.DataFrame()
    by = ["engine"] + (by or [])
    work = df.copy()
    work["ref_len"] = work["ref"].str.len().clip(lower=1)
    work["char_err"] = work["cer"] * work["ref_len"]
    grouped = work.groupby(by, sort=False)
    out = grouped.agg(
        samples=("sample_id", "count"),
        cer=("cer", "mean"),
        wer=("wer", "mean"),
        cer_strict=("cer_strict", "mean"),
        exact=("exact", "mean"),
        ms_per_line=("ms", "mean"),
        _err=("char_err", "sum"),
        _len=("ref_len", "sum"),
    ).reset_index()
    out["cer_micro"] = out["_err"] / out["_len"]
    out = out.drop(columns=["_err", "_len"])
    return out.sort_values(["cer"] if len(by) == 1 else by).reset_index(drop=True)


def pivot_cer(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Engine x `column` table of mean CER (for heatmaps and the README)."""
    if df.empty:
        return pd.DataFrame()
    table = df.pivot_table(index="engine", columns=column, values="cer", aggfunc="mean")
    preferred = [c for c in COLUMN_ORDER.get(column, []) if c in table.columns]
    rest = [c for c in table.columns if c not in preferred]
    return table[preferred + rest]


def _fmt(value, kind: str) -> str:
    if pd.isna(value):
        return "-"
    if kind == "pct":
        return f"{100 * value:.1f}%"
    if kind == "ms":
        return f"{value:.0f} ms"
    return str(value)


def to_markdown(table: pd.DataFrame, columns: dict[str, tuple[str, str]]) -> str:
    """Render selected columns as a GitHub markdown table.

    `columns` maps source column -> (header, kind) where kind is pct / ms / text.
    """
    headers = [h for h, _ in columns.values()]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for _, row in table.iterrows():
        cells = [_fmt(row[col], kind) for col, (_, kind) in columns.items()]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def leaderboard_markdown(df: pd.DataFrame, title: str = "") -> str:
    """Headline table plus a by-source and by-style breakdown, as markdown."""
    if df.empty:
        return "_No results yet. Run `urdulens benchmark`._"
    cols = {
        "engine": ("Engine", "text"),
        "samples": ("Lines", "text"),
        "cer": ("CER", "pct"),
        "wer": ("WER", "pct"),
        "exact": ("Exact lines", "pct"),
        "ms_per_line": ("Speed", "ms"),
    }
    parts = []
    if title:
        parts.append(f"**{title}**\n")
    parts.append(to_markdown(summarize(df), cols))
    for group, label in (("source", "Source"), ("style", "Style"), ("level", "Degradation")):
        if group in df.columns and df[group].nunique() > 1:
            table = pivot_cer(df, group)
            table = table.reset_index()
            cols_g = {"engine": ("Engine", "text")}
            cols_g.update({c: (f"{c}", "pct") for c in table.columns if c != "engine"})
            parts.append(f"\n**CER by {label.lower()}**\n")
            parts.append(to_markdown(table, cols_g))
    return "\n".join(parts)


def update_marked_block(text: str, block: str) -> str:
    """Replace the text between the leaderboard markers (markers are kept)."""
    if MARKER_START not in text or MARKER_END not in text:
        raise ValueError(f"Markers {MARKER_START} / {MARKER_END} not found")
    head, rest = text.split(MARKER_START, 1)
    _, tail = rest.split(MARKER_END, 1)
    return f"{head}{MARKER_START}\n{block}\n{MARKER_END}{tail}"
