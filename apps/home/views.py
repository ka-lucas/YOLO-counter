from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from apps.video_ao_vivo.models import CountingSession
from apps.cameras.models import Camera
from django.db.models import Sum, Count
from datetime import datetime, timedelta
from django.conf import settings
import json
import os
import psutil
import torch


class EmailLoginView(LoginView):
    template_name = "home/login.html"
    redirect_authenticated_user = True

    def form_invalid(self, form):
        messages.error(self.request, "Email ou senha inválidos.")
        return super().form_invalid(form)


@login_required
def home(request):
    # started_at é gravado com o relógio local "como UTC" (mesma convenção do resto do app)
    today = datetime.now().date()
    sessions = CountingSession.objects.filter(user=request.user, ended_at__isnull=False)

    def totals(day):
        t = sessions.filter(started_at__date=day).aggregate(i=Sum("total_in"), o=Sum("total_out"))
        return t["i"] or 0, t["o"] or 0

    def change(now_val, before_val):
        if before_val == 0:
            return 100 if now_val > 0 else 0
        return round((now_val - before_val) / before_val * 100)

    today_in, today_out = totals(today)
    yest_in, yest_out = totals(today - timedelta(days=1))

    daily_data = []
    for d in range(6, -1, -1):
        day = today - timedelta(days=d)
        day_in, day_out = totals(day)
        daily_data.append({"label": day.strftime("%d/%m"), "in": day_in, "out": day_out})

    # Detecções por minuto da sessão em andamento (log JSON do contador)
    minute_data = [0] * 10
    active = CountingSession.objects.filter(user=request.user, ended_at__isnull=True).first()
    if active and active.log_file_path:
        try:
            with open(os.path.join(settings.MEDIA_ROOT, active.log_file_path)) as f:
                events = json.load(f).get("events", [])
            now = datetime.now().replace(second=0, microsecond=0)
            for e in events:
                ago = (now - datetime.fromisoformat(e["timestamp"]).replace(second=0, microsecond=0)).total_seconds() // 60
                if 0 <= ago < 10:
                    minute_data[9 - int(ago)] += 1
        except (OSError, ValueError, KeyError):
            pass

    cameras = Camera.objects.filter(user=request.user, is_active=True)
    # Visão ao vivo: primeira câmera que o navegador consegue tocar direto (.mp4 servido por URL, não caminho de disco)
    preview_camera = next(
        (c for c in cameras
         if (c.primary_url or "").lower().endswith(".mp4") and c.primary_url.startswith(("/", "http"))),
        None,
    )

    gpu_available = torch.cuda.is_available()
    temp_usage = 52  # fallback quando o sistema não expõe sensores (Windows)
    try:
        for entries in (psutil.sensors_temperatures() or {}).values():
            if entries and entries[0].high:
                temp_usage = min(entries[0].current / entries[0].high * 100, 100)
                break
    except AttributeError:
        pass

    context = {
        "today_detected": today_in + today_out,
        "today_in": today_in,
        "today_out": today_out,
        "detected_change": change(today_in + today_out, yest_in + yest_out),
        "in_change": change(today_in, yest_in),
        "out_change": change(today_out, yest_out),
        "daily_data": daily_data,
        "minute_data": minute_data,
        "preview_camera": preview_camera,
        "gpu_available": gpu_available,
        "cpu_usage": psutil.cpu_percent(interval=0.2),
        "ram_usage": psutil.virtual_memory().percent,
        "temp_usage": temp_usage,
    }
    return render(request, "home/home.html", context)
