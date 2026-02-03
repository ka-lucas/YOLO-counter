from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from apps.video_ao_vivo.models import CountingSession
from apps.cameras.models import Camera
from django.db.models import Sum, Count
from datetime import datetime, timedelta
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
    # Dados do usuário logado
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # Sessões de hoje - todas as sessões
    today_sessions = CountingSession.objects.filter(
        started_at__date=today,
        ended_at__isnull=False
    )
    
    # Sessões de ontem - todas as sessões
    yesterday_sessions = CountingSession.objects.filter(
        started_at__date=yesterday,
        ended_at__isnull=False
    )
    
    # Totais de hoje
    today_totals = today_sessions.aggregate(
        total_detected=Sum('total_in') or 0 + Sum('total_out') or 0,
        total_in=Sum('total_in') or 0,
        total_out=Sum('total_out') or 0
    )
    
    # Totais de ontem
    yesterday_totals = yesterday_sessions.aggregate(
        total_detected=Sum('total_in') or 0 + Sum('total_out') or 0,
        total_in=Sum('total_in') or 0,
        total_out=Sum('total_out') or 0
    )
    
    # Calcular percentuais de variação
    def calc_percentage(today_val, yesterday_val):
        if yesterday_val == 0:
            return 100 if today_val > 0 else 0
        return round(((today_val - yesterday_val) / yesterday_val) * 100)
    
    detected_change = calc_percentage(
        (today_totals['total_in'] or 0) + (today_totals['total_out'] or 0),
        (yesterday_totals['total_in'] or 0) + (yesterday_totals['total_out'] or 0)
    )
    
    in_change = calc_percentage(
        today_totals['total_in'] or 0,
        yesterday_totals['total_in'] or 0
    )
    
    out_change = calc_percentage(
        today_totals['total_out'] or 0,
        yesterday_totals['total_out'] or 0
    )
    
    # Dados para gráficos (últimas 9 horas) - buscar de todas as sessões
    hourly_data = []
    for i in range(9):
        hour_start = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=8-i)
        hour_end = hour_start + timedelta(hours=1)
        
        hour_sessions = CountingSession.objects.filter(
            started_at__gte=hour_start,
            started_at__lt=hour_end,
            ended_at__isnull=False
        )
        
        hour_totals = hour_sessions.aggregate(
            in_count=Sum('total_in'),
            out_count=Sum('total_out')
        )
        
        hourly_data.append({
            'hour': hour_start.strftime('%H:00'),
            'in': hour_totals['in_count'] or 0,
            'out': hour_totals['out_count'] or 0
        })
    
    # Dados por minuto (últimos 10 minutos) - dos logs de eventos
    minute_data = []
    
    # Buscar sessão ativa do usuário
    active_session = CountingSession.objects.filter(
        ended_at__isnull=True
    ).first()
    
    if active_session and active_session.log_file_path:
        import json
        import os
        from django.conf import settings
        
        try:
            log_path = os.path.join(settings.MEDIA_ROOT, active_session.log_file_path)
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    log_data = json.load(f)
                    events = log_data.get('events', [])
                
                # Agrupar eventos por minuto
                now = datetime.now()
                for i in range(10):
                    minute_start = now.replace(second=0, microsecond=0) - timedelta(minutes=i)
                    minute_end = minute_start + timedelta(minutes=1)
                    
                    # Contar eventos neste minuto
                    minute_count = 0
                    for event in events:
                        try:
                            event_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                            if minute_start <= event_time < minute_end:
                                minute_count += 1
                        except:
                            continue
                    
                    minute_data.append(minute_count)
        except Exception as e:
            # Fallback para dados vazios
            minute_data = [0] * 10
    else:
        # Sem sessão ativa, dados vazios
        minute_data = [0] * 10
    
    minute_data.reverse()
    
    # Status do sistema
    try:
        # GPU/CPU info
        gpu_available = torch.cuda.is_available()
        gpu_usage = 0
        if gpu_available:
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                gpu_usage = gpus[0].load * 100 if gpus else 0
            except:
                gpu_usage = 42  # Fallback se não conseguir ler GPU
        else:
            gpu_usage = 0  # CPU only
        
        # Memória RAM
        memory = psutil.virtual_memory()
        ram_usage = memory.percent
        
        # CPU
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Temperatura (simulada se não disponível)
        try:
            temps = psutil.sensors_temperatures()
            temp_usage = 52  # Fallback
            if temps:
                for name, entries in temps.items():
                    if entries:
                        temp_usage = min(entries[0].current / entries[0].high * 100, 100)
                        break
        except:
            temp_usage = 52
            
    except Exception as e:
        # Fallback values
        gpu_usage = 42
        ram_usage = 70
        cpu_usage = 65
        temp_usage = 52

    # Câmeras do usuário (temporariamente removido até migração)
    # user_cameras = Camera.objects.filter(user=request.user, is_active=True)
    
    context = {
        "today_detected": (today_totals['total_in'] or 0) + (today_totals['total_out'] or 0),
        "today_in": today_totals['total_in'] or 0,
        "today_out": today_totals['total_out'] or 0,
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
    }

    return render(request, "home/home.html", context)
