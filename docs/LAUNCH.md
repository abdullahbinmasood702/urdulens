# Launch kit

Fill the `[brackets]` with **your own real numbers** from your own runs. Do not publish a claim you have not measured.
Avoid "first" or "nobody has ever": say what it *is* (open, reproducible, documented).

## GitHub "About" box (repo page -> gear icon)

Description (at least 100 characters, LinkedIn's Post Inspector warns below that):

> Open, reproducible benchmark that compares OCR engines on Urdu text lines, with a weekly automated leaderboard, a synthetic data generator, a trainable model and a photo reader app.

Website: your Render dashboard link.
Topics: `urdu`, `ocr`, `nlp`, `benchmark`, `python`, `streamlit`, `postgresql`, `github-actions`, `tesseract`, `easyocr`, `data-science`

## Social preview image

`assets/social-card.png` (1280x640, already generated with `urdulens card`).
Repo -> **Settings** -> **General** -> **Social preview** -> **Edit** -> upload. The repo must be public.
To see it: paste the repo URL in a WhatsApp chat (add `?v=2` to bypass cache) or use linkedin.com/post-inspector.

## LinkedIn post (draft)

> I wanted to know: how well can OCR actually read Urdu?
>
> Public Urdu OCR projects each report their own error rate on their own data, so they can't be compared. So I built UrduLens: a small open benchmark that scores OCR engines on the same lines and publishes a leaderboard every week.
>
> What the first run showed (synthetic lines, [N] of them):
> • EasyOCR: [13.6]% character error rate. Tesseract: [39.2]%.
> • Both do much worse on Nastaliq (the style most Pakistani print uses) than Naskh.
> • [one finding from YOUR real-image set once you have it]
>
> Caveat: synthetic images are easier than real photos, so the next step is a labeled set of real ones.
>
> Built with Python, GitHub Actions, PostgreSQL (Neon), Streamlit and open-source OCR engines, all on free tiers. Code, data and method are open: [repo link]
>
> If you work with Urdu text or OCR, I'd love your feedback, and contributions of real test lines.
>
> #Urdu #OCR #NLP #DataScience #OpenSource

## Article outline (Dev.to / Hashnode / LinkedIn article)

1. The problem: Urdu OCR numbers you cannot compare (link the three examples in the README).
2. Design: one line image in, text out; frozen test set; leakage control.
3. Scoring choices: normalisation, and why `cer_strict` exists.
4. What broke: the surprises (word merging, Tesseract returning nothing on heavy lines, Nastaliq).
5. What is still weak: synthetic vs real; how you are fixing it.
6. How to add an engine or contribute lines.
Include one chart from the dashboard (CER by style and level).

## Resume bullets (edit the numbers)

> Built UrduLens, an open benchmark for Urdu OCR: engine-agnostic Python framework, synthetic data generator (5 fonts, 3 degradation levels), CER/WER scoring with Unicode normalisation, automated weekly runs via GitHub Actions into Neon PostgreSQL, and a Streamlit leaderboard. Found EasyOCR at [13.6]% vs Tesseract at [39.2]% CER on [350] lines.

> Trained a CRNN/CTC line recogniser in PyTorch on synthetic data (free Kaggle GPU) and evaluated it against off-the-shelf engines on a hand-labeled real-image test set. [add real result]

## Before you post

- [ ] CI is green and the dashboard link works (mention the free-tier wake-up delay in the README)
- [ ] The README results table is from a real run you did
- [ ] Nothing private in the repo (no `.env`, no connection strings, no personal photos)
- [ ] You can explain every part in an interview: scoring, leakage control, why synthetic is not real
