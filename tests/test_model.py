import numpy as np
import pytest

torch = pytest.importorskip("torch")

from urdulens import charset, model, synth  # noqa: E402


def test_forward_shape_matches_output_length():
    net = model.CRNN().eval()
    x = torch.randn(2, 1, model.IMG_H, 301)
    y = net(x)
    assert y.shape == (2, model.output_length(301), charset.NUM_CLASSES)


def test_preprocess_and_collate_pad_with_paper():
    img = synth.make_sample(np.random.default_rng(0), "پانی", "lateef", "clean").image
    a = model.preprocess(img)
    b = model.preprocess(synth.make_sample(np.random.default_rng(1), "پانی پیجیے آج", "lateef", "clean").image)
    assert a.shape[1] == model.IMG_H
    batch, widths = model.collate_images([a, b])
    assert batch.shape == (2, 1, model.IMG_H, max(a.shape[-1], b.shape[-1]))
    short = int(widths.argmin())
    assert float(batch[short, 0, :, -1].min()) == 1.0 or a.shape[-1] == b.shape[-1]


def test_decode_logits_greedy():
    a, b = charset.CHAR2IDX["ا"], charset.CHAR2IDX["ب"]
    logits = torch.full((1, 6, charset.NUM_CLASSES), -5.0)
    for t, idx in enumerate([a, a, 0, b, b, 0]):
        logits[0, t, idx] = 5.0
    assert model.decode_logits(logits) == ["اب"]


def test_checkpoint_round_trip(tmp_path):
    net = model.CRNN()
    model.save_checkpoint(net, tmp_path / "m.pt", version="t")
    net2, meta = model.load_checkpoint(tmp_path / "m.pt")
    assert meta["version"] == "t"
    x = torch.randn(1, 1, model.IMG_H, 128)
    assert torch.allclose(net.eval()(x), net2(x), atol=1e-5)


def test_checkpoint_with_other_charset_is_rejected(tmp_path):
    net = model.CRNN()
    model.save_checkpoint(net, tmp_path / "m.pt")
    payload = torch.load(tmp_path / "m.pt", weights_only=True)
    payload["meta"]["charset"] = "xyz"
    torch.save(payload, tmp_path / "bad.pt")
    with pytest.raises(ValueError):
        model.load_checkpoint(tmp_path / "bad.pt")


@pytest.mark.slow
def test_can_overfit_a_tiny_batch():
    """Run with: pytest -m slow. Proves labels, visual order, CTC and decoding line up."""
    from torch import nn

    from urdulens import metrics, train
    from urdulens.textorder import to_logical

    torch.manual_seed(0)
    x, widths, targets, tl, texts = train.collate(list(train.LineDataset("train", 7, n=3)))
    net = model.CRNN()
    ctc = nn.CTCLoss(blank=0, zero_infinity=True)
    opt = torch.optim.AdamW(net.parameters(), lr=3e-3)
    for _ in range(350):
        loss = train._ctc_loss(net, x, widths, targets, tl, ctc)
        opt.zero_grad()
        loss.backward()
        opt.step()
    net.eval()
    with torch.no_grad():
        preds = model.decode_logits(net(x), widths)
    errs = sum(metrics.score_pair(r, to_logical(p)).char_errors for p, r in zip(preds, texts))
    assert errs <= 0.05 * sum(len(t) for t in texts)
