"""UrduLens leaderboard dashboard (deploy this one on Render).

    streamlit run apps/dashboard.py
"""

from __future__ import annotations

import html
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from _common import RTL_CSS
from sqlalchemy import text

from urdulens import report, store
from urdulens.paths import BENCHMARK_DIR

st.set_page_config(page_title="UrduLens leaderboard", page_icon="📖", layout="wide")
st.markdown(RTL_CSS, unsafe_allow_html=True)


@st.cache_data(ttl=600, show_spinner="Loading results (a sleeping free database can take ~30 s)...")
def load_all() -> tuple[pd.DataFrame, pd.DataFrame]:
    engine = store.get_engine()
    try:
        return store.load_runs(engine), store.load_results(engine)
    except Exception:
        # Tables missing: nothing has been stored yet.
        return pd.DataFrame(), pd.DataFrame()


@st.cache_data(ttl=3600)
def load_manifest_paths() -> dict[str, str]:
    paths: dict[str, str] = {}
    for name in ("synthetic_manifest.csv", "real_manifest.csv"):
        p = BENCHMARK_DIR / name
        if p.exists():
            m = pd.read_csv(p, dtype=str, keep_default_na=False)
            paths.update({row["id"]: str(BENCHMARK_DIR / row["path"]) for _, row in m.iterrows()})
    return paths


st.title("📖 UrduLens: how well can OCR read Urdu?")
st.caption(
    "Open benchmark of OCR engines on Urdu text lines. Lower error is better. "
    "CER = character error rate, WER = word error rate."
)

runs, results = load_all()
if results.empty:
    if st.button("Refresh data"):
        st.cache_data.clear()
        st.rerun()
    st.info(
        "No benchmark results in the database yet. Run `urdulens benchmark` "
        "(see the README), then refresh this page."
    )
    st.stop()

with st.sidebar:
    if st.button("Refresh data"):
        st.cache_data.clear()
        st.rerun()
    st.header("Filters")
    run_labels = {int(r.id): f"#{r.id}  {str(r.created_at)[:16]}  ({r.dataset}, {r.n_samples} lines)" for r in runs.itertuples()}
    run_id = st.selectbox("Benchmark run", list(run_labels), format_func=run_labels.get)
    data = results[results["run_id"] == run_id]
    sources = sorted(data["source"].unique())
    source_pick = st.multiselect("Image source", sources, default=sources)
    styles = sorted(data["style"].dropna().unique())
    style_pick = st.multiselect("Script style", styles, default=styles)
    ctypes = sorted(data["content_type"].dropna().unique())
    ctype_pick = st.multiselect("Content", ctypes, default=ctypes)
    data = data[data["source"].isin(source_pick) & data["style"].isin(style_pick) & data["content_type"].isin(ctype_pick)]

if data.empty:
    st.warning("No lines match these filters.")
    st.stop()

if "synthetic" in set(data["source"]) and "real" not in set(data["source"]):
    st.warning(
        "These results use **synthetic** images (rendered text with simulated blur/noise), "
        "not real photographs. Treat them as a controlled comparison, not real-world accuracy."
    )

summary = report.summarize(data)
best = summary.iloc[0]
c1, c2, c3 = st.columns(3)
c1.metric("Best engine (lowest CER)", str(best["engine"]))
c2.metric("Its CER", f"{100 * best['cer']:.1f}%")
c3.metric("Lines scored", f"{int(data['sample_id'].nunique())}")

tab_board, tab_break, tab_hist, tab_err = st.tabs(["Leaderboard", "Breakdown", "History", "Error explorer"])

with tab_board:
    show = summary.rename(
        columns={"engine": "Engine", "samples": "Lines", "cer": "CER", "wer": "WER", "exact": "Exact lines", "ms_per_line": "ms / line"}
    )[["Engine", "Lines", "CER", "WER", "Exact lines", "ms / line"]]
    st.dataframe(
        show.style.format({"CER": "{:.1%}", "WER": "{:.1%}", "Exact lines": "{:.1%}", "ms / line": "{:.0f}"}),
        hide_index=True,
        use_container_width=True,
    )
    fig = px.bar(summary, x="engine", y="cer", text=summary["cer"].map(lambda v: f"{v:.1%}"), labels={"cer": "CER", "engine": ""})
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "CER is averaged per line. Text is normalised before scoring (look-alike Arabic/Urdu letters, "
        "diacritics, digit style, punctuation), see docs/METHODOLOGY.md."
    )

with tab_break:
    group = st.radio("Break down by", ["level", "style", "font", "content_type", "source"], horizontal=True)
    pivot = report.pivot_cer(data, group)
    if not pivot.empty:
        fig = px.imshow(pivot, text_auto=".1%", aspect="auto", color_continuous_scale="RdYlGn_r", labels=dict(color="CER"))
        st.plotly_chart(fig, use_container_width=True)

with tab_hist:
    if len(runs) < 2:
        st.info("History appears after two or more benchmark runs (the weekly workflow adds one each week).")
    else:
        hist = results.merge(runs[["id", "created_at"]], left_on="run_id", right_on="id")
        hist = hist.groupby(["created_at", "engine"], as_index=False)["cer"].mean()
        fig = px.line(hist, x="created_at", y="cer", color="engine", markers=True)
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

with tab_err:
    engine_pick = st.selectbox("Engine", sorted(data["engine"].unique()))
    worst = data[data["engine"] == engine_pick].sort_values("cer", ascending=False).head(15)
    paths = load_manifest_paths()
    for _, row in worst.iterrows():
        left, right = st.columns([1, 2])
        img_path = paths.get(row["sample_id"])
        if img_path and Path(img_path).exists():
            left.image(img_path, caption=f"{row['sample_id']} · {row['font']} · {row['level']}")
        right.markdown(f"**CER {row['cer']:.0%}**")
        right.markdown(f"<div class='urdu-box'>{html.escape(row['ref'])}</div>", unsafe_allow_html=True)
        right.markdown(f"<div class='urdu-box'>{html.escape(row['hyp']) or '(nothing read)'}</div>", unsafe_allow_html=True)
        st.divider()

with st.expander("Database"):
    try:
        with store.get_engine().connect() as conn:
            n = conn.execute(text("SELECT COUNT(*) FROM results")).scalar()
        st.write(f"{n} stored line results across {len(runs)} runs.")
    except Exception as exc:  # pragma: no cover
        st.write(f"Database check failed: {exc}")
