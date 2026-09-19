"""UrduLens Reader: upload a photo of Urdu text, get editable text back.

    streamlit run apps/reader.py

Runs anywhere Tesseract and/or EasyOCR are installed (locally, or on a free
Hugging Face Space, see docs/GUIDE.md). Images are processed in memory and are
never saved.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
from _common import RTL_CSS
from PIL import Image, ImageOps

from urdulens import engines
from urdulens.paths import RESULTS_DIR

st.set_page_config(page_title="UrduLens Reader", page_icon="📖")
st.markdown(RTL_CSS, unsafe_allow_html=True)
st.title("📖 UrduLens Reader")
st.caption("Photo of Urdu text in, editable text out. Your image is processed in memory and never stored.")

READER_ENGINES = ["tesseract", "easyocr", "paddleocr"]


@st.cache_resource(show_spinner="Loading OCR engine (first time can take a minute)...")
def get_engine(name: str):
    return engines.create(name)


def best_engine_from_results() -> str | None:
    """Engine with the lowest CER in the latest benchmark, if a result file exists."""
    path = Path(RESULTS_DIR) / "latest_scores.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    real = df[df["source"] == "real"]
    df = real if not real.empty else df
    ranked = df.groupby("engine")["cer"].mean().sort_values()
    for name in ranked.index:
        if name in READER_ENGINES:
            return name
    return None


available: list[str] = []
unavailable: dict[str, str] = {}
for name in READER_ENGINES:
    ok, reason = engines.check(name)
    if ok:
        available.append(name)
    else:
        unavailable[name] = reason

if not available:
    st.error("No OCR engine is installed here. Install Tesseract with Urdu data (see docs/GUIDE.md).")
    st.stop()

best = best_engine_from_results()
default_idx = available.index(best) if best in available else 0
engine_name = st.selectbox("OCR engine", available, index=default_idx)
if best:
    st.caption(f"Lowest error on the latest benchmark run: **{best}**")
for name, reason in unavailable.items():
    st.caption(f"{name}: not available ({reason})")

mode = st.radio("What is in the picture?", ["A page or several lines", "Exactly one line"], horizontal=True)
source = st.radio("Image from", ["Upload a file", "Use the camera"], horizontal=True)
if source == "Upload a file":
    file = st.file_uploader("Urdu image", type=["png", "jpg", "jpeg", "webp", "bmp"])
else:
    file = st.camera_input("Take a photo of the Urdu text")

if file is not None:
    image = Image.open(file)
    image = ImageOps.exif_transpose(image).convert("RGB")
    st.image(image, caption="Your image", use_container_width=True)
    with st.expander("Improve difficult photos"):
        boost = st.checkbox("Auto-contrast", value=True)
        upscale = st.checkbox("Enlarge small images (2x)", value=max(image.size) < 900)
    work = image
    if boost:
        work = ImageOps.autocontrast(work.convert("L"), cutoff=1).convert("RGB")
    if upscale:
        work = work.resize((work.width * 2, work.height * 2), Image.LANCZOS)

    if st.button("Read the text", type="primary"):
        with st.spinner("Reading..."):
            engine = get_engine(engine_name)
            text = engine.read_line(work) if mode == "Exactly one line" else engine.read_document(work)
        if not text.strip():
            st.warning("Nothing was read. Try a sharper photo, better light, or the other engine.")
        else:
            edited = st.text_area("Recognised text (you can edit it)", value=text, height=240)
            st.download_button("Download as .txt", edited.encode("utf-8"), file_name="urdu_text.txt", mime="text/plain")
            st.caption("OCR for Urdu is imperfect, especially on Nastaliq print and low-quality photos. Check the result.")
