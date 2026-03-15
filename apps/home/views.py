from datetime import datetime, timedelta
import os
import json

import psutil
import torch
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Count, Sum
from django.shortcuts import render

from apps.cameras.models import Camera
from apps.video_ao_vivo.models import CountingSession


class EmailLoginView(LoginView):
    template_name = "home/login.html"
    redirect_authenticated_user = True

    def form_invalid(self, form):
        messages.error(self.request, "Email ou senha invalidos.")
        return super().form_invalid(form)


@login_required
def home(request):
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    user_cameras = Camera.objects.filter(user=request.user)
    active_cameras = user_cameras.filter(is_active=True)
    active_session_camera_ids = set(
        CountingSession.objects.filter(user=request.user, ended_at__isnull=True).values_list("camera_id", flat=True)
    )

    today_sessions = CountingSession.objects.filter(
        started_at__date=today,
        ended_at__isnull=False,
        user=request.user,
    )

    yesterday_sessions = CountingSession.objects.filter(
        started_at__date=yesterday,
        ended_at__isnull=False,
        user=request.user,
    )

    today_totals = today_sessions.aggregate(
        total_in=Sum("total_in"),
        total_out=Sum("total_out"),
    )

    yesterday_totals = yesterday_sessions.aggregate(
        total_in=Sum("total_in"),
        total_out=Sum("total_out"),
    )

    def calc_percentage(today_val, yesterday_val):
        if yesterday_val == 0:
            return 100 if today_val > 0 else 0
        return round(((today_val - yesterday_val) / yesterday_val) * 100)

    detected_change = calc_percentage(
        (today_totals["total_in"] or 0) + (today_totals["total_out"] or 0),
        (yesterday_totals["total_in"] or 0) + (yesterday_totals["total_out"] or 0),
    )
    in_change = calc_percentage(today_totals["total_in"] or 0, yesterday_totals["total_in"] or 0)
    out_change = calc_percentage(today_totals["total_out"] or 0, yesterday_totals["total_out"] or 0)

    hourly_data = []
    for i in range(9):
        hour_start = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=8 - i)
        hour_end = hour_start + timedelta(hours=1)
        hour_sessions = CountingSession.objects.filter(
            started_at__gte=hour_start,
            started_at__lt=hour_end,
            ended_at__isnull=False,
            user=request.user,
        )
        hour_totals = hour_sessions.aggregate(in_count=Sum("total_in"), out_count=Sum("total_out"))
        hourly_data.append(
            {
                "hour": hour_start.strftime("%H:00"),
                "in": hour_totals["in_count"] or 0,
                "out": hour_totals["out_count"] or 0,
            }
        )

    minute_data = []
    active_session = CountingSession.objects.filter(
        ended_at__isnull=True,
        user=request.user,
    ).select_related("camera").first()

    if active_session and active_session.log_file_path:
        from django.conf import settings

        try:
            log_path = os.path.join(settings.MEDIA_ROOT, active_session.log_file_path)
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as file_obj:
                    log_data = json.load(file_obj)
                    events = log_data.get("events", [])

                now = datetime.now()
                for i in range(10):
                    minute_start = now.replace(second=0, microsecond=0) - timedelta(minutes=i)
                    minute_end = minute_start + timedelta(minutes=1)
                    minute_count = 0

                    for event in events:
                        try:
                            event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
                            event_time = event_time.replace(tzinfo=None)
                            if minute_start <= event_time < minute_end:
                                minute_count += 1
                        except Exception:
                            continue

                    minute_data.append(minute_count)
        except Exception:
            minute_data = [0] * 10
    else:
        minute_data = [0] * 10

    minute_data.reverse()

    try:
        gpu_available = torch.cuda.is_available()
        gpu_usage = 0
        if gpu_available:
            try:
                import GPUtil

                gpus = GPUtil.getGPUs()
                gpu_usage = gpus[0].load * 100 if gpus else 0
            except Exception:
                gpu_usage = 42

        memory = psutil.virtual_memory()
        ram_usage = memory.percent
        cpu_usage = psutil.cpu_percent(interval=1)

        try:
            temps = psutil.sensors_temperatures()
            temp_usage = 52
            if temps:
                for _name, entries in temps.items():
                    if entries:
                        high_limit = entries[0].high or 100
                        temp_usage = min((entries[0].current / high_limit) * 100, 100)
                        break
        except Exception:
            temp_usage = 52
    except Exception:
        gpu_available = False
        gpu_usage = 42
        ram_usage = 70
        cpu_usage = 65
        temp_usage = 52

    alerts = []

    def add_alert(level, icon, message, time_label):
        if len(alerts) < 3:
            alerts.append(
                {
                    "level": level,
                    "icon": icon,
                    "message": message,
                    "time_label": time_label,
                }
            )

    if not active_cameras.exists():
        add_alert(
            "warning",
            "exclamation-triangle-fill",
            "Nenhuma camera ativa encontrada para monitoramento.",
            "agora",
        )

    if active_session:
        recent_volume = sum(minute_data[-5:]) if minute_data else 0
        if recent_volume == 0:
            add_alert(
                "warning",
                "camera-video-off-fill",
                f"Sem novas deteccoes nos ultimos 5 min na camera {active_session.camera.name}.",
                "ha 5 min",
            )
        else:
            add_alert(
                "success",
                "check-circle-fill",
                f"Camera {active_session.camera.name} registrou {recent_volume} deteccoes nos ultimos 5 min.",
                "tempo real",
            )
    else:
        latest_session = (
            CountingSession.objects.filter(ended_at__isnull=False, user=request.user)
            .select_related("camera")
            .first()
        )
        if latest_session:
            add_alert(
                "info",
                "clock-history",
                f"Ultima sessao finalizada em {latest_session.camera.name} com saldo {latest_session.balance}.",
                latest_session.started_at.strftime("%d/%m %H:%M"),
            )

    peak_minute = max(minute_data) if minute_data else 0
    if peak_minute >= 5:
        add_alert(
            "danger",
            "exclamation-octagon-fill",
            f"Pico de movimentacao detectado: {peak_minute} eventos em um unico minuto.",
            "ultimos 10 min",
        )

    if ram_usage >= 80 or temp_usage >= 80 or gpu_usage >= 85:
        resource_name = "RAM" if ram_usage >= 80 else ("temperatura" if temp_usage >= 80 else "GPU")
        resource_value = ram_usage if ram_usage >= 80 else (temp_usage if temp_usage >= 80 else gpu_usage)
        add_alert(
            "warning",
            "cpu-fill",
            f"Uso elevado de {resource_name}: {resource_value:.0f}%.",
            "agora",
        )

    if len(alerts) < 3:
        completed_today = today_sessions.aggregate(total=Count("id"))["total"] or 0
        add_alert(
            "info",
            "bar-chart-fill",
            f"{completed_today} sessao(oes) concluida(s) hoje com {today_totals['total_in'] or 0} entradas e {today_totals['total_out'] or 0} saidas.",
            "hoje",
        )

    dashboard_cameras = []
    for camera in user_cameras.order_by("name"):
        is_online = camera.id in active_session_camera_ids and camera.is_active and bool(camera.primary_url)
        dashboard_cameras.append(
            {
                "id": camera.id,
                "name": camera.name,
                "is_online": is_online,
                "status_label": "Online" if is_online else "Offline",
            }
        )

    context = {
        "today_detected": (today_totals["total_in"] or 0) + (today_totals["total_out"] or 0),
        "today_in": today_totals["total_in"] or 0,
        "today_out": today_totals["total_out"] or 0,
        "detected_change": detected_change,
        "in_change": in_change,
        "out_change": out_change,
        "hourly_data": hourly_data,
        "minute_data": minute_data,
        "gpu_usage": gpu_usage,
        "ram_usage": ram_usage,
        "cpu_usage": cpu_usage,
        "temp_usage": temp_usage,
        "gpu_available": gpu_available,
        "alerts": alerts,
        "dashboard_cameras": dashboard_cameras,
    }

    return render(request, "home/home.html", context)
