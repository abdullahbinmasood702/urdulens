"""Shared bits for the Streamlit apps."""

from __future__ import annotations

import sys
from pathlib import Path

# Lets `streamlit run apps/x.py` work without installing the package (e.g. on Render).
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RTL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;500&display=swap');
.urdu, .urdu-box { direction: rtl; text-align: right; font-family: 'Noto Nastaliq Urdu', 'Noto Naskh Arabic', serif; line-height: 2.2; }
.urdu-box { font-size: 1.25rem; padding: .4rem .8rem; border-radius: .5rem; background: rgba(128,128,128,.10); }
textarea { direction: rtl; font-family: 'Noto Nastaliq Urdu', 'Noto Naskh Arabic', serif !important; font-size: 1.2rem !important; }
input[type="text"].rtl-input { direction: rtl; }
</style>
"""
