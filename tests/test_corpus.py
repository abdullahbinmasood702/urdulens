from urdulens import corpus


def test_splits_are_disjoint_and_cover_everything():
    parts = {s: set(corpus.sentences_for(s)) for s in corpus.SPLITS}
    assert not (parts["train"] & parts["test"])
    assert not (parts["train"] & parts["val"])
    assert not (parts["val"] & parts["test"])
    assert set().union(*parts.values()) == set(corpus.load_sentences())


def test_split_is_deterministic():
    s = corpus.load_sentences()[0]
    assert corpus.split_of(s) == corpus.split_of(s)


def test_enough_sentences_for_the_benchmark():
    assert len(corpus.sentences_for("test")) >= 20
    assert len(corpus.sentences_for("train")) >= 80


def test_random_line_is_nonempty_and_reproducible():
    import numpy as np

    a = [corpus.random_line(np.random.default_rng(3)) for _ in range(5)]
    b = [corpus.random_line(np.random.default_rng(3)) for _ in range(5)]
    assert a == b and all(a)


def test_train_words_only_come_from_train_sentences():
    train_words = set(corpus.vocabulary("train"))
    assert train_words
    for s in corpus.sentences_for("train"):
        assert set(s.split()) <= train_words
