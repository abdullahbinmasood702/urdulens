# Training the UrduLens model

The bundled model is a small CRNN (about 2.6 M parameters): a convolutional feature extractor, two bidirectional
LSTM layers, and CTC decoding. It is trained on synthetic lines generated on the fly (5 fonts, 3 degradation levels,
real sentences + word shuffles + numbers) and can optionally be fine-tuned on your real training lines.

Honest expectation: a model trained only on synthetic renders **will not beat mature engines on real photos**. Its
value here is a transparent baseline, a place to try improvements, and a way to show the train / benchmark loop.

## What was verified before shipping

* Tiny-batch overfit test: the network reaches 0% CER on 4 fixed lines after ~350 CPU steps. This proves labels,
  left-to-right visual ordering, CTC loss and decoding are consistent. (`pytest -m slow`.)
* A 6-step training run ran end to end (loop, validation, checkpoint, engine wrapper).
* **No full training run was done** by the author of this repo (no GPU available while building). The numbers a
  full run reaches are yours to report.

## Train on Kaggle (free GPU)

1. Push this repo to GitHub first (public).
2. kaggle.com -> Create -> **New Notebook** -> File -> **Import Notebook** -> upload `train/kaggle_train.ipynb`.
3. Right panel: **Accelerator = GPU (T4 or P100)**, **Internet = On** (Kaggle asks you to verify your phone).
4. Edit the `git clone` URL if your GitHub username differs, then **Run All**. 20,000 steps takes about an hour.
   Watch `validation CER` fall; it stays near 100% for the first 1-2 thousand steps (normal for CTC).
5. When it finishes, download `models/urdulens_crnn.pt` from the **Output** panel.
6. Put it in `models/` in your local repo (it is gitignored) and run
   `urdulens benchmark --engines tesseract,easyocr,urdulens-crnn`.
7. Publish the file as a **GitHub Release** asset so others can download it. Do not commit weights to git.

Optional experiment tracking: create a free Weights & Biases account, add `WANDB_API_KEY` in Kaggle Secrets, and add
`--wandb-project urdulens` to the train command.

## Train locally

```powershell
pip install -e ".[train]"
urdulens train --steps 20000 --batch-size 32 --device auto
```
On a CPU this is very slow; use it only for experiments with `--steps 300`.

## Improve it

In rough order of likely payoff:

1. **Real data**: label real lines (`docs/LABELING.md`) and train with `--use-real`. Judge only on the real test split.
2. **More text**: put extra Urdu sentences in `data/corpus/extra/*.txt` (gitignored, split automatically). A larger
   vocabulary matters more than more steps.
3. **More fonts** (open licences only): add to `fonts/` and `urdulens/fonts.py`.
4. **Harder augmentation**: `urdulens/augment.py` (perspective, ink bleed, background textures).
5. A bigger network or a transformer recogniser. Add the new model as another engine so it competes on the same leaderboard.
