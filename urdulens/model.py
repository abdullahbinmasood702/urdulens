"""CRNN line recogniser: small CNN -> BiLSTM -> CTC.

The image is scanned left to right, so labels are converted to *visual* order
(see textorder.py) for training and the decoded string is converted back to
logical order for the user.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageOps
from torch import nn

from urdulens import charset
from urdulens.textorder import to_logical

IMG_H = 64  # fixed input height (the CNN collapses it to 1)
MAX_W = 1024  # very long lines are squeezed to this width
WIDTH_STRIDE = 2  # time steps = width // 2


class CRNN(nn.Module):
    def __init__(self, num_classes: int = charset.NUM_CLASSES, hidden: int = 192, dropout: float = 0.1):
        super().__init__()

        def block(cin: int, cout: int) -> list[nn.Module]:
            return [nn.Conv2d(cin, cout, 3, padding=1, bias=False), nn.BatchNorm2d(cout), nn.ReLU(inplace=True)]

        layers: list[nn.Module] = []
        layers += block(1, 32) + [nn.MaxPool2d(2, 2)]  # H 64 -> 32, W / 2
        layers += block(32, 64) + [nn.MaxPool2d((2, 1), (2, 1))]  # H 32 -> 16
        layers += block(64, 128) + block(128, 128) + [nn.MaxPool2d((2, 1), (2, 1))]  # H 16 -> 8
        layers += block(128, 192) + block(192, 192) + [nn.MaxPool2d((2, 1), (2, 1))]  # H 8 -> 4
        layers += [nn.Conv2d(192, 256, kernel_size=(4, 1), bias=False), nn.BatchNorm2d(256), nn.ReLU(inplace=True)]
        self.cnn = nn.Sequential(*layers)
        self.rnn = nn.LSTM(256, hidden, num_layers=2, bidirectional=True, batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden * 2, num_classes)
        self.hidden = hidden

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B, 1, 64, W) -> logits (B, T, num_classes) with T = W // 2."""
        feats = self.cnn(x)  # (B, 256, 1, W/2)
        feats = feats.squeeze(2).permute(0, 2, 1)  # (B, T, 256)
        out, _ = self.rnn(feats)
        return self.fc(out)


def output_length(width: int) -> int:
    return width // WIDTH_STRIDE


def preprocess(image: Image.Image) -> torch.Tensor:
    """PIL image -> normalised tensor (1, IMG_H, W); dark text on light paper."""
    img = ImageOps.autocontrast(image.convert("L"), cutoff=1)
    w, h = img.size
    new_w = int(min(MAX_W, max(16, round(w * IMG_H / max(h, 1)))))
    img = img.resize((new_w, IMG_H), Image.BILINEAR)
    arr = (np.asarray(img, dtype=np.float32) / 255.0 - 0.5) / 0.5
    return torch.from_numpy(arr).unsqueeze(0)


def collate_images(images: list[torch.Tensor]) -> tuple[torch.Tensor, torch.Tensor]:
    """Pad a list of (1, H, W) tensors to a common width with 'paper' (1.0)."""
    widths = torch.tensor([im.shape[-1] for im in images], dtype=torch.long)
    max_w = int(widths.max())
    batch = torch.ones(len(images), 1, IMG_H, max_w)
    for i, im in enumerate(images):
        batch[i, :, :, : im.shape[-1]] = im
    return batch, widths


def decode_logits(logits: torch.Tensor, widths: torch.Tensor | None = None) -> list[str]:
    """Greedy CTC decoding of (B, T, C) logits into visual-order strings."""
    best = logits.argmax(dim=-1).cpu()
    texts = []
    for b in range(best.shape[0]):
        seq = best[b]
        if widths is not None:
            seq = seq[: output_length(int(widths[b]))]
        texts.append(charset.decode_indices(charset.ctc_collapse(seq.tolist())))
    return texts


@torch.no_grad()
def predict_line(net: CRNN, image: Image.Image, device: str = "cpu") -> str:
    net.eval()
    x, widths = collate_images([preprocess(image)])
    logits = net(x.to(device))
    return to_logical(decode_logits(logits, widths)[0])


def save_checkpoint(net: CRNN, path: Path | str, **meta) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "state_dict": {k: v.cpu() for k, v in net.state_dict().items()},
        "meta": {"charset": charset.CHARS, "hidden": net.hidden, "img_h": IMG_H, **meta},
    }
    torch.save(payload, path)


def load_checkpoint(path: Path | str, device: str = "cpu") -> tuple[CRNN, dict]:
    payload = torch.load(Path(path), map_location=device, weights_only=True)
    meta = payload["meta"]
    if meta.get("charset") != charset.CHARS:
        raise ValueError(
            "This checkpoint was trained with a different character set. "
            "Retrain the model or use the matching version of UrduLens."
        )
    net = CRNN(hidden=int(meta.get("hidden", 192)))
    net.load_state_dict(payload["state_dict"])
    net.to(device).eval()
    return net, meta
