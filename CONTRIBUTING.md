# Contributing

Thanks for helping make Urdu OCR measurable.

Good first contributions:
- **A new engine**: see `docs/ADDING_AN_ENGINE.md`. Keep it optional and lazily imported.
- **Real test lines**: photos of Urdu print you own (or that are public domain / CC0), cropped to one line each,
  with no personal information. See `docs/LABELING.md`.
- **More Urdu sentences** for `data/corpus/sentences_ur.txt` (original text only, no copyrighted material).

Before opening a pull request:

```bash
pip install -e ".[db,app,dev]"
ruff check .
pytest -q
```

Do not add anything to `data/benchmark/` test sets that also appears in training data. The tests check this.
