"""Usuário neutro + câmeras com vídeos locais + sessões fictícias para gravar demo.

Vídeos: baixe clipes de licença aberta (ex.: Pexels) para media/videos/
(demo.mp4, bovinos.mp4, suinos.mp4).

Idempotente: rodar de novo recria as sessões do usuário demo.
    python scripts/seed_demo.py
"""
import os
import random
import sys
from datetime import datetime, timedelta, timezone as dt_tz

import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from apps.cameras.models import Camera  # noqa: E402
from apps.video_ao_vivo.models import CountingSession  # noqa: E402

EMAIL, PASSWORD = "demo@yolocounter.app", "demo2026"

CAMERAS = [
    # nome, vídeo, classe YOLO, tipo de animal
    ("Corredor de Embarque 01", "media/videos/demo.mp4", 0, "Suínos"),
    ("Curral de Bovinos", "media/videos/bovinos.mp4", 19, "Bovinos"),
    ("Baia de Suínos 02", "media/videos/suinos.mp4", 0, "Suínos"),
]
RECIPIENTS = [
    "Frigorífico Vale Verde",
    "Cooperativa Agro Sul",
    "Granja Boa Esperança",
    "Agropecuária Horizonte",
]


def main():
    random.seed(42)
    User = get_user_model()
    user = User.objects.filter(email=EMAIL).first() or User.objects.create_superuser(email=EMAIL, password=PASSWORD)

    cams = []
    for name, video, cls, animal in CAMERAS:
        cam, _ = Camera.objects.update_or_create(
            user=user, name=name,
            defaults={"rtsp_url": os.path.join(BASE_DIR, video), "location": "Unidade Demo",
                      "detection_class": cls, "is_active": True},
        )
        cams.append((cam, animal))

    # Só reprodução: o navegador toca o arquivo servido em /media (sem detecção)
    Camera.objects.update_or_create(
        user=user, name="Câmera Entrada Principal",
        defaults={"rtsp_url": "/media/videos/demo.mp4", "location": "Unidade Demo", "is_active": True},
    )

    CountingSession.objects.filter(user=user).delete()

    # O dashboard compara com datetime.now() ingênuo, que o Django lê como UTC;
    # gravamos o horário local "como UTC" para os gráficos baterem com o relógio.
    now = datetime.now().replace(tzinfo=dt_tz.utc)
    starts = [now - timedelta(hours=h, minutes=random.randint(5, 50)) for h in range(1, 9)]
    starts += [now - timedelta(days=d, hours=random.randint(6, 18)) for d in range(1, 15) for _ in range(random.randint(6, 9))]

    for i, start in enumerate(sorted(starts)):
        cam, animal = random.choice(cams)
        total_in = random.randint(40, 320) if animal == "Suínos" else random.randint(15, 90)
        total_out = random.randint(0, max(1, total_in // 12))
        s = CountingSession.objects.create(
            user=user, camera=cam, total_in=total_in, total_out=total_out, balance=total_in - total_out,
            animal_type=animal, model_used="yolov8n.pt", line_y_norm=0.5,
            batch_number=f"LT-{start:%Y%m}-{i + 1:04d}", recipient=random.choice(RECIPIENTS),
        )
        # started_at é auto_now_add: só dá pra sobrescrever via update
        CountingSession.objects.filter(pk=s.pk).update(
            started_at=start, ended_at=start + timedelta(minutes=random.randint(12, 55)))

    print(f"{EMAIL} / {PASSWORD} | {len(cams)} câmeras | {len(starts)} sessões")


if __name__ == "__main__":
    main()
