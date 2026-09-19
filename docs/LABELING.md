# Adding real test lines (the part that makes the benchmark credible)

Goal: 100-200 lines from at least 15 different pages or photos, mixing Nastaliq and Naskh, photos and scans.
About 2 hours the first time.

## What to photograph

Use text **you have the right to use** and that contains **no personal information**:

* pages you printed yourself (type Urdu text, print it, photograph it under different light)
* your own notes, posters, signboards you photographed in public, textbook pages you own for private testing
* public-domain or openly licensed material

Avoid: names, CNIC/ID numbers, phone numbers, addresses, account numbers, bills, medical papers, other people's
private messages. If in doubt, leave it out.

Take some photos badly on purpose (tilt, shadow, distance): the benchmark should include real mess.

## Prepare the images

1. Crop **one line of text per image** (Windows Photos "Edit -> Crop", Paint, or any phone editor). Leave a small margin.
2. Save as PNG or JPG into `data/benchmark/real/images/`, named `<page>_line01.png`, `<page>_line02.png` ...
   (for example `poster1_line01.png`). The part before `_line` is the **group**: all lines from one page share it.

## Label them

```powershell
python -m streamlit run apps/labeler.py
```

For each image type exactly what it says (keep punctuation; no diacritics needed), choose style (nastaliq/naskh) and
type (photo/scan), press **Save and next**. Characters the model cannot use are rejected with an explanation.
Labels are saved to `data/benchmark/real/labels.csv`.

## Build the manifest

```powershell
urdulens prepare-real
```

It lists any problems (missing files, unsupported characters, duplicate names) and writes
`data/benchmark/real_manifest.csv`. Lines are split **by group**: roughly 70% test, 20% train, 10% validation.
Only `test` lines are used by `urdulens benchmark`; `train` lines can be mixed into training (`--use-real`).

Then run the benchmark again: `urdulens benchmark --dataset all`.

## Publishing your real set (optional)

By default `.gitignore` keeps your images, labels and real manifest **private**. To publish them, delete the four lines
under "private data" in `.gitignore`, double-check every image for personal information and copyright, then commit.
The weekly workflow will then include the real set automatically.
