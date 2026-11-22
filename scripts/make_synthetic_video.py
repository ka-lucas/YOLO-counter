"""Gera um vídeo sintético para testar o pipeline sem depender de vídeos externos.

Recorta pessoas da imagem de exemplo da Ultralytics (bus.jpg) e as move sobre um fundo neutro:
uma desce e outra sobe, cruzando a linha horizontal do meio. Contagem esperada: 1 em cada sentido.

Uso: python scripts/make_synthetic_video.py saida.mp4
"""
import os
import sys

import cv2
import numpy as np
import ultralytics

out_path = sys.argv[1] if len(sys.argv) > 1 else "synthetic.mp4"
img = cv2.imread(os.path.join(os.path.dirname(ultralytics.__file__), "assets", "bus.jpg"))
# Caixas aproximadas de duas pessoas em bus.jpg (810x1080)
person_a = img[405:880, 50:245]
person_b = img[395:905, 665:810]

W, H, N = 960, 720, 120
writer = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), 30, (W, H))
for i in range(N):
    frame = np.full((H, W, 3), 200, np.uint8)
    cv2.rectangle(frame, (0, H // 2 + 200), (W, H), (170, 170, 170), -1)
    t = i / (N - 1)
    for crop, x, y in ((person_a, 200, int(-120 + t * 760)),      # desce
                       (person_b, 650, int(560 - t * 760))):      # sobe
        h, w = crop.shape[:2]
        y0, y1 = max(y - h, 0), min(y, H)
        if y1 > y0:
            frame[y0:y1, x:x + w] = crop[h - (y1 - y0) if y - h < 0 else 0:(h - (y1 - y0) if y - h < 0 else 0) + (y1 - y0)]
    writer.write(frame)
writer.release()
print(out_path)
