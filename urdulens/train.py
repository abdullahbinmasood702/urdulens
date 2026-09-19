"""Train the CRNN on synthetic Urdu lines (optionally mixed with your real labeled lines).

Runs anywhere; use a GPU (free Kaggle or Colab) for real training runs. See docs/TRAINING.md.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, IterableDataset, get_worker_info

from urdulens import augment, charset, corpus, dataset, metrics, model, synth
from urdulens.paths import DEFAULT_MODEL
from urdulens.textorder import to_logical, to_visual

LEVEL_PROBS = {"clean": 0.25, "mild": 0.45, "heavy": 0.30}


class LineDataset(IterableDataset):
    """Endless (or fixed-size) stream of (image_tensor, target_indices, text) triples."""

    def __init__(
        self,
        split: str,
        seed: int,
        n: int | None = None,
        real_rows: pd.DataFrame | None = None,
        real_prob: float = 0.3,
    ):
        self.split, self.seed, self.n = split, seed, n
        self.real_rows = real_rows if real_rows is not None and len(real_rows) else None
        self.real_prob = real_prob

    def __iter__(self):
        info = get_worker_info()
        worker = info.id if info else 0
        rng = np.random.default_rng([self.seed, worker])
        levels, probs = list(LEVEL_PROBS), list(LEVEL_PROBS.values())
        count = 0
        while self.n is None or count < self.n:
            if self.real_rows is not None and rng.random() < self.real_prob:
                row = self.real_rows.iloc[int(rng.integers(0, len(self.real_rows)))]
                with Image.open(row["abs_path"]) as im:
                    img = augment.degrade(im.convert("L"), "mild", rng)
                text = row["text"]
            else:
                text = corpus.random_line(rng, self.split)
                level = str(rng.choice(levels, p=probs))
                img = synth.make_sample(rng, text, level=level).image
            target = charset.encode(to_visual(text))
            if not target:
                continue
            count += 1
            yield model.preprocess(img), torch.tensor(target, dtype=torch.long), text


def collate(batch):
    images, targets, texts = zip(*batch)
    x, widths = model.collate_images(list(images))
    target_lengths = torch.tensor([len(t) for t in targets], dtype=torch.long)
    return x, widths, torch.cat(targets), target_lengths, list(texts)


def _ctc_loss(net, x, widths, targets, target_lengths, ctc) -> torch.Tensor:
    logits = net(x)  # (B, T, C)
    log_probs = logits.float().log_softmax(dim=-1).permute(1, 0, 2)  # (T, B, C)
    input_lengths = torch.clamp(widths // model.WIDTH_STRIDE, max=log_probs.shape[0])
    return ctc(log_probs, targets, input_lengths, target_lengths)


@torch.no_grad()
def evaluate(net, loader, device) -> float:
    """Micro-averaged CER (normalized) over a fixed validation loader."""
    net.eval()
    errors = total = 0
    for x, widths, _t, _l, texts in loader:
        preds = model.decode_logits(net(x.to(device)), widths)
        for pred, ref in zip(preds, texts):
            score = metrics.score_pair(ref, to_logical(pred))
            errors += score.char_errors
            total += score.char_total
    net.train()
    return errors / max(total, 1)


def train(
    steps: int = 20000,
    batch_size: int = 32,
    lr: float = 1e-3,
    device: str = "auto",
    out: Path | str = DEFAULT_MODEL,
    val_every: int = 1000,
    val_size: int = 200,
    log_every: int = 100,
    workers: int = 2,
    seed: int = 0,
    real_manifest: Path | str | None = None,
    wandb_project: str | None = None,
) -> Path:
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(seed)
    real_rows = None
    if real_manifest and Path(real_manifest).exists():
        df = dataset.load_manifest(real_manifest)
        real_rows = df[df["split"] == "train"].reset_index(drop=True)
        print(f"Mixing in {len(real_rows)} real training lines")

    net = model.CRNN().to(device)
    print(f"Parameters: {sum(p.numel() for p in net.parameters()) / 1e6:.2f} M | device: {device}")
    ctc = nn.CTCLoss(blank=charset.BLANK, zero_infinity=True)
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=1e-2)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=steps, pct_start=0.1)
    use_amp = device == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    train_loader = DataLoader(
        LineDataset("train", seed, real_rows=real_rows),
        batch_size=batch_size,
        collate_fn=collate,
        num_workers=workers,
        persistent_workers=workers > 0,
    )
    val_loader = DataLoader(LineDataset("val", 12345, n=val_size), batch_size=32, collate_fn=collate)

    run = None
    if wandb_project:
        import wandb

        run = wandb.init(project=wandb_project, config=dict(steps=steps, batch_size=batch_size, lr=lr))

    best_cer, running, t0 = float("inf"), 0.0, time.time()
    net.train()
    for step, (x, widths, targets, target_lengths, _texts) in enumerate(train_loader, start=1):
        x = x.to(device)
        with torch.autocast(device_type="cuda", enabled=use_amp):
            loss = _ctc_loss(net, x, widths, targets, target_lengths, ctc)
        opt.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()
        scaler.unscale_(opt)
        nn.utils.clip_grad_norm_(net.parameters(), 5.0)
        scaler.step(opt)
        scaler.update()
        sched.step()
        running += loss.item()
        if step % log_every == 0:
            avg = running / log_every
            running = 0.0
            print(f"step {step:6d}/{steps} loss {avg:.3f} lr {sched.get_last_lr()[0]:.2e} {time.time() - t0:.0f}s")
            if run:
                run.log({"loss": avg}, step=step)
        if step % val_every == 0 or step == steps:
            cer = evaluate(net, val_loader, device)
            print(f"  validation CER {cer:.4f}")
            if run:
                run.log({"val_cer": cer}, step=step)
            if cer < best_cer:
                best_cer = cer
                model.save_checkpoint(net, out, steps=step, val_cer=cer, version=f"step{step}")
                print(f"  saved {out}")
        if step >= steps:
            break
    if run:
        run.finish()
    print(f"Done. Best validation CER {best_cer:.4f} (synthetic validation lines, not real photos).")
    return Path(out)
