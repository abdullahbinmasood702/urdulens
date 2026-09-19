# Methodology

What the benchmark measures, how, and where it can mislead you. Read this before quoting a number.

## Task

**Line recognition**: given an image of exactly one line of Urdu text, return the text.
This isolates *reading* from *finding text on a page* (detection, layout, line order), which are
separate problems. Engines are called through `OCREngine.read_line`.
Full-page reading is supported by the Reader app but is **not benchmarked yet**.

## Datasets

| Set | What | Purpose |
|---|---|---|
| `synthetic` (350 lines, frozen) | Test sentences and number lines rendered with 5 open fonts, 3 degradation levels | Controlled, reproducible comparison; breakdowns by font, script style and image quality |
| `real` (yours) | Cropped lines from real photos/scans that you label | The number that actually matters. Empty until you add data (`docs/LABELING.md`) |

Composition of `synthetic`: 20 held-out sentences x 5 fonts x 3 levels (300 lines) + 10 number/date/price
lines x 5 fonts at the mild level (50 lines). Images and `synthetic_manifest.csv` are committed so the set never
changes silently. `urdulens build-benchmark` regenerates it deterministically (per-row seeds), but pixel-exact
output can differ slightly across Pillow/FreeType versions, so use the committed files for comparisons.

### Leakage control

* Sentences are split into train / val / test by a **hash of the sentence text** (70/10/20), so the split is the
  same on every machine and cannot drift when the file is edited.
* Benchmark text comes only from the **test** split. Word-shuffle training lines use words from the **train**
  split only. `tests/test_dataset.py` fails if a benchmark sentence also appears in train/val.
* Real lines are split by **group** (the page or photo they came from), so lines from one page never sit in both
  train and test.

### Synthetic image levels

| Level | What is applied |
|---|---|
| clean | rendered text with margin |
| mild | rotation up to 1.5 degrees, blur (sigma 0.3-0.8), light gradient, noise (sigma 3-8), JPEG quality 70-92 |
| heavy | rotation up to 3 degrees, shear up to 0.12, downscale to 45-70% and back, blur (sigma 0.8-1.6), strong gradient, noise (sigma 8-16), JPEG quality 35-60 |

Exact code: `urdulens/augment.py`.

## Scoring

Both hypothesis and reference are normalised first (`urdulens/normalize.py`):

* Unicode NFKC, invisible characters (ZWNJ, bidi marks) removed, whitespace collapsed
* Look-alike letters unified: Arabic yeh/alef maksura to Urdu ye, Arabic kaf to Urdu kaf, Arabic heh to heh goal
* Diacritics and tatweel removed
* Digits (Arabic-Indic, Urdu, ASCII) mapped to ASCII
* Urdu punctuation mapped to ASCII (`۔` to `.`, `،` to `,`, `؟` to `?`)

Why: engines trained on Arabic often emit U+064A where Urdu keyboards use U+06CC. Both render almost identically,
and a reader would not call it a reading error. The dashboard also stores `cer_strict` (NFKC and whitespace only)
so you can see how much of an engine's error is just encoding habit.

Metrics:

* **CER** = character edit distance / reference length, computed per line, then averaged with equal weight per line.
  A micro-average (total edits / total characters) is kept as `cer_micro`. CER can exceed 100%.
* **WER** = same at word level (words split on spaces). Urdu spacing is ambiguous (words are often typed without
  a space), so WER is noisier than CER.
* **Exact lines** = share of lines with zero normalised errors.
* **Speed** = mean wall-clock milliseconds per line on the machine that ran it (not comparable across machines).

## Engines and settings

| Engine | Setting |
|---|---|
| Tesseract | `-l urd --psm 7`, 20 px white border added. The `urd` model is whatever the installed package ships (the `tesseract-ocr-urd` Ubuntu package or the tessdata you chose on Windows); the version string is stored with every run |
| EasyOCR | Urdu recognition model (`ur`), **recognition only** on the whole line image (detection skipped, so it is scored on reading, like the others) |
| PaddleOCR | experimental Arabic-script model wrapper; not verified by the author |
| urdulens-crnn | this repo's model, greedy CTC decoding; only present after you train one |

No engine is tuned for this benchmark. Defaults were used except where a setting is needed to read a single line.

## Limitations (please read)

1. **Synthetic is not real.** Rendered text with simulated blur is easier and more uniform than a shaky phone photo of a
   newspaper. Use synthetic results to compare engines *against each other* under controlled conditions, not to
   claim real-world accuracy. Real accuracy needs the real set.
2. **Font coverage.** Jameel Noori Nastaleeq, the font of most Pakistani print, is not openly licensed and is
   not included. Noto Nastaliq Urdu and Gulzar are close but not identical.
3. **Small and narrow text.** 20 distinct sentences plus 10 number/date/price lines, everyday topics, no diacritics, little English, no
   handwriting, one line at a time. Differences of a couple of points between engines are not meaningful.
4. **Normalisation is a choice.** It favours engines that emit Arabic-variant letters. `cer_strict` shows the other view.
5. **Versions matter.** Results describe the exact engine versions recorded in each run and will change as they update.
6. **Models trained on synthetic data** (including this repo's CRNN) can overfit to the fonts they saw. Fine-tune on
   real lines (`docs/TRAINING.md`) and judge only on the real test split.
