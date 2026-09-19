"""1280x640 GitHub social-preview card (shown when the repo link is shared).

Layout adapted from the free-for-dev toolkit card; the right-hand panel shows a
rendered Urdu line (an *input* sample), never invented results.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from urdulens import synth

S = 2  # supersampling for smooth edges
FONT_DIRS = [
    "/usr/share/fonts/truetype/google-fonts/",
    "/usr/share/fonts/truetype/liberation/",
    "/usr/share/fonts/truetype/dejavu/",
    "C:/Windows/Fonts/",
    "/Library/Fonts/",
]
FALLBACK = {
    "Bold": ["Poppins-Bold.ttf", "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"],
    "Medium": ["Poppins-Medium.ttf", "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"],
    "Regular": ["Poppins-Regular.ttf", "LiberationSans-Regular.ttf", "DejaVuSans.ttf", "arial.ttf", "Arial.ttf"],
}


def _font(weight: str, size: int) -> ImageFont.ImageFont:
    for name in FALLBACK[weight]:
        for folder in FONT_DIRS:
            path = Path(folder) / name
            if path.exists():
                return ImageFont.truetype(str(path), int(size * S))
    return ImageFont.load_default()


def make_card(
    title: str,
    subtitle: str,
    name: str,
    org: str,
    pills: list[str],
    logo: Path | None,
    out: Path,
    sample_text: str = "اردو کی سطر پڑھنے کا امتحان۔",
    accent: str = "#0969da",
) -> Path:
    W, H = 1280 * S, 640 * S
    r = lambda v: int(v * S)  # noqa: E731
    img = Image.new("RGB", (W, H), "#ffffff")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, r(10)], fill=accent)

    x_text = 80
    if logo and Path(logo).exists():
        lg = Image.open(logo).convert("RGBA")
        bbox = lg.getchannel("A").getbbox()
        if bbox:
            lg = lg.crop(bbox)
        lg = lg.resize((r(68), r(68)), Image.LANCZOS)
        img.paste(lg, (r(80), r(50)), lg)
        x_text = 80 + 68 + 18
    if name:
        d.text((r(x_text), r(56)), name, font=_font("Bold", 21), fill="#1f2328")
    if org:
        d.text((r(x_text), r(86)), org, font=_font("Medium", 18), fill=accent)

    y = 158
    words = title.split()
    lines = [title] if len(words) < 2 else [" ".join(words[:1]), " ".join(words[1:])]
    for line in lines:
        d.text((r(80), r(y)), line, font=_font("Bold", 66), fill="#1f2328")
        y += 74

    yy = y + 24  # subtitle sits just under the title, whatever its line count
    wrapped = textwrap.wrap(subtitle, 36)[:3]
    for line in wrapped:
        d.text((r(80), r(yy)), line, font=_font("Regular", 27), fill="#59636e")
        yy += 40

    # right panel: a rendered Urdu line
    x0, y0, x1, y1 = 790, 130, 1200, 460
    d.rounded_rectangle([r(x0), r(y0), r(x1), r(y1)], radius=r(18), fill="#f6f8fa", outline="#d1d9e0", width=r(2))
    d.text((r(x0 + 26), r(y0 + 20)), "Input: one line of Urdu", font=_font("Medium", 18), fill="#1f2328")
    line_img = synth.render_line(sample_text, "noto-nastaliq", 88, weight=500, fg=25, bg=246, pad_x=10, pad_y=10)
    max_w = r(x1 - x0 - 60)
    scale = min(1.0, max_w / line_img.width)
    line_img = line_img.resize((int(line_img.width * scale), int(line_img.height * scale)), Image.LANCZOS)
    px = r(x0) + (r(x1 - x0) - line_img.width) // 2
    py = r(y0) + (r(y1 - y0) - line_img.height) // 2 + r(10)
    img.paste(line_img.convert("RGB"), (px, py))
    d.text((r(x0 + 26), r(y1 - 44)), "then: which OCR engine reads it best?", font=_font("Regular", 16), fill="#59636e")

    x = 80
    pf = _font("Medium", 21)
    for pill in pills:
        w = d.textlength(pill, font=pf) / S + 40
        d.rounded_rectangle([r(x), r(500), r(x + w), r(548)], radius=r(24), fill="#ddf4ff", outline="#b6e3ff", width=r(2))
        d.text((r(x + 20), r(509)), pill, font=pf, fill="#0550ae")
        x += w + 14

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.resize((1280, 640), Image.LANCZOS).save(out, optimize=True)
    return out
