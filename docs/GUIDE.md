# UrduLens: from zip to published (Windows, beginner level)

Follow the parts in order. After each step there is a line telling you what success looks like.
If something fails, copy the **last 10 lines of the error** (never passwords or connection strings) and ask for help.

Time: Parts 1-4 about 45 minutes. Parts 5-8 about 1-2 hours. Real data and training come later.

---

## Part 1: Set up your computer

1. Install **Python 3.10 or newer** from python.org. On the first screen tick **Add python.exe to PATH**.
2. Install **Git** from git-scm.com (keep the defaults).
3. Install **Tesseract**: open the page `github.com/UB-Mannheim/tesseract/wiki`, download the newest Windows installer, run it.
   On the "Choose Components" screen open **Additional language data** and tick **Urdu**. Keep the default folder
   `C:\Program Files\Tesseract-OCR`.
4. Unzip `urdulens.zip`. Open the `urdulens` folder in File Explorer, click the address bar, type `powershell`, press Enter.
5. Check the tools:
   ```powershell
   python --version
   git --version
   & "C:\Program Files\Tesseract-OCR\tesseract.exe" --list-langs
   ```
   Success: versions print, and the language list includes `urd`.

## Part 2: Install and run the first benchmark

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[db,app,dev]"
urdulens benchmark --engines tesseract --limit 30 --no-store
```
Success: a small table with one row (`tesseract`) and a CER percentage. (`--limit 30` scores 30 random lines as a quick test.)
If you see `Skipping tesseract: Tesseract binary not found`, set the path for this window:
`$env:TESSERACT_CMD="C:\Program Files\Tesseract-OCR\tesseract.exe"` and run it again.

Now the full run and the dashboard:
```powershell
urdulens benchmark --engines tesseract
python -m streamlit run apps/dashboard.py
```
Success: a browser tab opens at `localhost:8501` showing the leaderboard. Press `Ctrl+C` in PowerShell to stop.

Optional second engine (large download, several GB with PyTorch):
```powershell
pip install easyocr
urdulens benchmark --engines tesseract,easyocr
```
The first EasyOCR run downloads its models and takes several minutes; 350 lines take roughly 5-10 minutes on a laptop CPU.

## Part 3: Try the Reader

```powershell
python -m streamlit run apps/reader.py
```
Upload a photo of Urdu print. Success: the recognised text appears in a box you can edit and download.

## Part 4: Run the tests

```powershell
pytest -q
ruff check .
```
Success: about `60 passed, 1 skipped` (65 if PyTorch is installed; the Tesseract test skips itself if Tesseract is missing) and `All checks passed!`.

## Part 5: Publish on GitHub

1. github.com -> **+** -> **New repository** -> name `urdulens`, **Public**, tick nothing else -> **Create repository**.
2. In PowerShell (inside the `urdulens` folder):
   ```powershell
   git init
   git add .
   git commit -m "UrduLens: open Urdu OCR benchmark"
   git branch -M main
   git remote add origin https://github.com/<your-username>/urdulens.git
   git push -u origin main
   ```
   If your GitHub username is not `abdullahbinmasood702`, search the repo for that text and replace it with yours
   (README badge and links, `train/kaggle_train.ipynb`, `deploy/hf-space/README.md`).
3. **Use `git push`, not the browser's "upload files" button**: the browser upload skips dot-folders such as `.github`, which holds the workflows.
   (No terminal? GitHub Desktop also works and includes dot-folders.)
4. Open the **Actions** tab. The **CI** workflow should start and turn green within a few minutes. If it is red, open it, click the failed step, read the log.
   Success: green tick. The badge at the top of the README now works.

## Part 6: Database on Neon (so results persist and the dashboard has data)

1. neon.tech -> sign up -> **Create project** (name `urdulens`, pick the nearest region, keep only **Postgres** on).
2. Skip the "Set up Neon with your coding agent" screen -> **Go to project**.
3. Click **Connect** (top right). Turn on **Show password**, keep pooling on, click **Copy snippet**. The string looks like
   `postgresql://user:PASSWORD@ep-xxxx-pooler.region.aws.neon.tech/neondb?sslmode=require`.
   Treat it like a password. Never paste it into a chat, a file in the repo, or a screenshot.
   If a later error mentions `channel_binding`, delete `&channel_binding=require` from the string.
4. Create the tables and store a run (the variable lasts only for this PowerShell window):
   ```powershell
   $env:DATABASE_URL="paste-your-string-here"
   urdulens init-db
   urdulens benchmark --engines tesseract
   ```
   Success: `Stored run #1 in postgresql...`. In Neon -> **Tables** you see `runs` and `results`.
5. GitHub repo -> **Settings** -> **Secrets and variables** -> **Actions** (under Security, not the plain "Actions" item) -> **New repository secret**:
   name `DATABASE_URL`, value = your string.
6. **Actions** tab -> **Weekly benchmark** -> **Run workflow**. The first run takes 15-40 minutes (it installs PyTorch and EasyOCR).
   Success: green tick, a new commit "Update leaderboard" appears, and the README table refreshes. From now on it runs every Monday.
   (Scheduled workflows pause after 60 days without repo activity; the weekly commit prevents that.)

## Part 7: Dashboard on Render

1. render.com -> **New** -> **Web Service** -> connect your GitHub repo.
2. Runtime **Python**, instance type **Free**.
3. Build command: `pip install -r requirements-dashboard.txt`
4. Start command: `streamlit run apps/dashboard.py --server.port $PORT --server.address 0.0.0.0`
5. Environment: add `DATABASE_URL` with your Neon string. **Deploy**.
   Success: a public `onrender.com` link showing the leaderboard. Free services sleep when idle (first visit can take about a minute) and Neon
   auto-suspends too. Say this in your README so nobody thinks it is broken. Put the link in the repo's **About -> Website** field.

## Part 8: Reader on a Hugging Face Space (free)

1. Build the upload folder: `urdulens space` (creates `dist/hf-space`).
2. huggingface.co -> **New** -> **Space** -> name `urdulens-reader`, SDK **Streamlit**, hardware **CPU basic (free)**, public.
3. **Files** -> **Add file** -> **Upload files**: drag the *contents* of `dist/hf-space`. Commit.
4. The Space builds (installs Tesseract, PyTorch and EasyOCR) which can take 10-20 minutes the first time.
   Success: the Reader opens in the Space. Add its link to the README.

## Part 9: Real test lines and training (next sessions)

* Real photos: `docs/LABELING.md`. This is what turns the benchmark from "controlled" into "credible".
* Train the model on a free GPU: `docs/TRAINING.md`.

## Part 10: Make it look professional

Everything is in `docs/LAUNCH.md`: repo description and topics, social preview image (`assets/social-card.png`, already generated),
LinkedIn post, article outline and resume bullets.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `KeyError: 'DATABASE_URL'` or results not in Neon | the variable is set per PowerShell window; set it again, or the Actions secret is missing |
| `SSL` or connection errors | the string must contain `sslmode=require`; try removing `&channel_binding=require` |
| `Skipping tesseract: ... Urdu data ('urd') is missing` | re-run the Tesseract installer and tick **Urdu** under Additional language data |
| `Skipping easyocr: easyocr is not installed` | `pip install easyocr` |
| EasyOCR very slow the first time | it is downloading models; later runs are faster |
| `.github` missing on GitHub | you used browser upload; use `git push` or GitHub Desktop |
| Workflow red X | open the run, click the failed step, read the log; network blips often fix themselves on the next run |
| Render app crashes on boot | check the logs: usually missing `DATABASE_URL` or a wrong start command |
| Dashboard says "No benchmark results" | run `urdulens benchmark` with the same `DATABASE_URL`, then click **Refresh data** |
| Urdu looks disconnected/broken in a window | your terminal font cannot shape Urdu; the images, apps and README are fine |
