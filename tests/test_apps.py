import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from urdulens import store  # noqa: E402
from urdulens.paths import ROOT  # noqa: E402


def _run(name, timeout=30):
    import streamlit as st

    st.cache_data.clear()
    st.cache_resource.clear()
    return AppTest.from_file(str(ROOT / "apps" / name), default_timeout=timeout).run()


def test_dashboard_empty_state(sqlite_url):
    at = _run("dashboard.py")
    assert not at.exception
    assert any("No benchmark results" in i.value for i in at.info)


def test_dashboard_with_results(sqlite_url):
    row = dict(engine="e", engine_version="1", sample_id="syn0000", source="synthetic", content_type="sentence",
               style="naskh", font="lateef", level="clean", ref="اردو", hyp="ارد", cer=0.25, wer=1.0,
               cer_strict=0.25, exact=False, ms=5.0)
    eng = store.init_db()
    store.save_run(eng, "synthetic", [row])
    at = _run("dashboard.py")
    assert not at.exception
    assert any("synthetic" in w.value for w in at.warning)


def test_reader_starts_without_upload():
    at = _run("reader.py")
    assert not at.exception


def test_labeler_starts_without_images():
    at = _run("labeler.py")
    assert not at.exception
