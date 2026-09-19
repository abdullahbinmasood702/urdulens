"""Label real Urdu line images for the benchmark.

    streamlit run apps/labeler.py

Put cropped line images (one line of text each) in data/benchmark/real/images/,
open this app, type what each line says, and press Save. Labels are written to
data/benchmark/real/labels.csv. Then run `urdulens prepare-real`.
"""

from __future__ import annotations

import csv

import streamlit as st
from _common import RTL_CSS
from PIL import Image

from urdulens import charset, normalize
from urdulens.paths import REAL_BENCH_DIR

IMAGES = REAL_BENCH_DIR / "images"
LABELS = REAL_BENCH_DIR / "labels.csv"
FIELDS = ["file", "text", "style", "level", "group"]

st.set_page_config(page_title="UrduLens labeler", page_icon="✍️")
st.markdown(RTL_CSS, unsafe_allow_html=True)
st.title("✍️ Label real Urdu lines")


def read_labels() -> dict[str, dict]:
    if not LABELS.exists():
        return {}
    with LABELS.open(encoding="utf-8", newline="") as f:
        return {r["file"]: r for r in csv.DictReader(f)}


def write_label(row: dict) -> None:
    new = not LABELS.exists()
    LABELS.parent.mkdir(parents=True, exist_ok=True)
    with LABELS.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


files = sorted(p.name for p in IMAGES.glob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}) if IMAGES.exists() else []
done = read_labels()
todo = [f for f in files if f not in done]

st.progress(len(done) / len(files) if files else 0.0, text=f"{len(done)} labeled, {len(todo)} to go")

if not files:
    st.info(f"No images yet. Put line images in `{IMAGES}` and reload. See docs/LABELING.md.")
    st.stop()
if not todo:
    st.success("All images are labeled. Now run `urdulens prepare-real` in your terminal.")
    st.stop()

current = todo[0]
st.image(Image.open(IMAGES / current), caption=current, use_container_width=True)
with st.form(key=f"label-{current}", clear_on_submit=True):
    text = st.text_input("What does this line say? (type it exactly, in Urdu)")
    c1, c2, c3 = st.columns(3)
    style = c1.selectbox("Script style", ["nastaliq", "naskh"])
    level = c2.selectbox("Image type", ["photo", "scan"])
    group = c3.text_input("Page / photo id", value=current.split("_line")[0])
    save = st.form_submit_button("Save and next", type="primary")

if save:
    clean = normalize.strict(text)
    unknown = charset.unknown_chars(clean)
    if not clean:
        st.error("Type the text first.")
    elif unknown:
        shown = " ".join(f"{c} (U+{ord(c):04X})" for c in sorted(unknown))
        st.error(f"These characters are not supported (remove diacritics or unusual symbols): {shown}")
    else:
        write_label(dict(file=current, text=clean, style=style, level=level, group=group))
        st.rerun()
