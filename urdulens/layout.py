"""Reading-order helpers for right-to-left text boxes."""

from __future__ import annotations

from collections.abc import Sequence


def _center_and_height(box: Sequence) -> tuple[float, float, float]:
    """(x_center, y_center, height) of a polygon or [x0, x1, y0, y1] box."""
    if len(box) == 4 and not hasattr(box[0], "__len__"):
        x0, x1, y0, y1 = box
        return (x0 + x1) / 2, (y0 + y1) / 2, abs(y1 - y0)
    xs = [p[0] for p in box]
    ys = [p[1] for p in box]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(ys) - min(ys)


def assemble_rtl(items: Sequence[tuple[Sequence, str]]) -> str:
    """Join detected (box, text) pieces into text lines in Urdu reading order.

    Lines run top to bottom; inside a line, pieces run right to left.
    """
    pieces = []
    for box, text in items:
        text = (text or "").strip()
        if not text:
            continue
        cx, cy, h = _center_and_height(box)
        pieces.append((cx, cy, max(h, 1.0), text))
    if not pieces:
        return ""
    pieces.sort(key=lambda p: p[1])
    heights = sorted(p[2] for p in pieces)
    tolerance = 0.6 * heights[len(heights) // 2]

    lines: list[list[tuple[float, float, float, str]]] = []
    for piece in pieces:
        if lines:
            mean_y = sum(p[1] for p in lines[-1]) / len(lines[-1])
            if abs(piece[1] - mean_y) <= tolerance:
                lines[-1].append(piece)
                continue
        lines.append([piece])
    out = []
    for line in lines:
        line.sort(key=lambda p: -p[0])
        out.append(" ".join(p[3] for p in line))
    return "\n".join(out)
