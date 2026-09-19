from urdulens import normalize


def test_arabic_letters_are_unified():
    # Arabic yeh, kaf and heh -> Urdu ye, kaf and heh goal
    assert normalize.normalized("كيف هذا") == "\u06a9\u06cc\u0641 \u06c1\u0630\u0627"


def test_digits_and_punctuation_unified():
    assert normalize.normalized("٤٥ ۴۵ 45") == "45 45 45"
    assert normalize.normalized("ہے۔") == normalize.normalized("ہے.")
    assert normalize.normalized("کیا؟") == "کیا?"


def test_diacritics_and_invisibles_removed():
    assert normalize.normalized("زَبَر") == normalize.normalized("زبر")
    assert normalize.strict("ا\u200bب\u200c") == "اب"


def test_whitespace_collapsed():
    assert normalize.strict("  ایک   دو \n تین ") == "ایک دو تین"


def test_idempotent():
    s = "لاہور میں آج ۳۴ ڈگری، ہے۔ كيف"
    once = normalize.normalized(s)
    assert normalize.normalized(once) == once


def test_composed_letters_survive():
    # alef-madda and yeh-with-hamza must not be split or stripped
    assert normalize.normalized("آئینہ") == "آئینہ"


def test_strict_keeps_letter_variants():
    assert normalize.strict("كيف") != normalize.strict("کیف")
