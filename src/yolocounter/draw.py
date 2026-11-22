"""Desenho da linha, das caixas e do placar sobre o quadro."""
from __future__ import annotations

import cv2
import numpy as np

from .geometry import Line

GREEN, RED, WHITE, BLACK, YELLOW = (60, 200, 60), (60, 60, 230), (255, 255, 255), (0, 0, 0), (0, 215, 255)


def draw_frame(frame: np.ndarray, line: Line, tracks, totals: dict, flash: bool = False) -> np.ndarray:
    out = frame.copy()
    p1 = tuple(int(v) for v in line.start)
    p2 = tuple(int(v) for v in line.end)
    cv2.line(out, p1, p2, YELLOW if flash else RED, 3)

    for track_id, (x1, y1, x2, y2), label in tracks:
        cv2.rectangle(out, (int(x1), int(y1)), (int(x2), int(y2)), GREEN, 2)
        text = f"{label} #{track_id}"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        top = int(y1) if y1 - th - 6 >= 0 else int(y1) + th + 6  # rótulo para dentro se a caixa encosta no topo
        top = max(top, th + 6)
        cv2.rectangle(out, (int(x1), top - th - 6), (int(x1) + tw + 4, top), GREEN, -1)
        cv2.putText(out, text, (int(x1) + 2, top - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, BLACK, 1, cv2.LINE_AA)

    lines = [f"Entradas: {totals['in']}", f"Saidas: {totals['out']}", f"Total: {totals['total']}"]
    cv2.rectangle(out, (8, 8), (190, 18 + 26 * len(lines)), BLACK, -1)
    for i, t in enumerate(lines):
        cv2.putText(out, t, (16, 34 + 26 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.7, WHITE, 2, cv2.LINE_AA)
    return out
