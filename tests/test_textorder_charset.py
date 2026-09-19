from urdulens import charset, corpus, textorder


def test_bidi_round_trip_on_whole_corpus():
    bad = [s for s in corpus.load_sentences() if textorder.to_logical(textorder.to_visual(s)) != s]
    assert bad == []


def test_numbers_keep_their_internal_order():
    visual = textorder.to_visual("نمبر 123")
    assert "123" in visual  # digits stay left-to-right inside the reversed line


def test_corpus_fits_charset():
    for s in corpus.load_sentences():
        assert not charset.unknown_chars(s), s


def test_charset_has_unique_entries_and_blank_zero():
    assert len(set(charset.CHARS)) == len(charset.CHARS)
    assert charset.BLANK == 0 and min(charset.CHAR2IDX.values()) == 1


def test_encode_decode_round_trip():
    s = "ہے 12 ab"
    assert charset.decode_indices(charset.encode(s)) == s


def test_ctc_collapse():
    a, b = charset.CHAR2IDX["ا"], charset.CHAR2IDX["ب"]
    assert charset.ctc_collapse([0, a, a, 0, a, b, b, 0]) == [a, a, b]
    assert charset.ctc_collapse([]) == []
