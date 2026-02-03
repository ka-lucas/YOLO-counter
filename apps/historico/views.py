from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from apps.video_ao_vivo.models import CountingSession
import logging

logger = logging.getLogger(__name__)


@login_required
def historico(request):
    """
    Página de histórico com sessões de contagem
    """
    # Filtros
    camera_filter = request.GET.get("camera", "")
    date_filter = request.GET.get("date", "")
    animal_filter = request.GET.get("animal", "")

    # Query base - apenas sessões finalizadas do usuário logado
    sessions = CountingSession.objects.filter(
        ended_at__isnull=False,
        user=request.user
    ).select_related('user', 'camera')

    # Aplicar filtros
    if camera_filter:
        sessions = sessions.filter(camera__id=camera_filter)
    if date_filter:
        sessions = sessions.filter(started_at__date=date_filter)
    if animal_filter:
        sessions = sessions.filter(camera__detection_class_name=animal_filter)

    # Paginação
    paginator = Paginator(sessions, 20)
    page = request.GET.get("page")
    sessions_page = paginator.get_page(page)

    # Log da visualização
    logger.info(f"Usuário {request.user.email} acessou histórico de contagens")
    
    # Câmeras usadas pelo usuário
    user_cameras = CountingSession.objects.filter(
        user=request.user,
        ended_at__isnull=False
    ).values_list('camera__id', 'camera__name').distinct().order_by('camera__name')

    # Tipos de animal distintos a partir das câmeras do usuário
    from apps.cameras.models import Camera
    animal_types = (
        Camera.objects.filter(user=request.user, is_active=True)
        .exclude(detection_class_name__exact='')
        .values_list('detection_class_name', flat=True)
        .distinct()
        .order_by('detection_class_name')
    )
    
    # Dados para gráficos
    from django.db.models import Sum, Count
    from datetime import datetime, timedelta
    
    # Últimos 7 dias do usuário logado
    last_7_days = datetime.now().date() - timedelta(days=7)
    recent_sessions = CountingSession.objects.filter(
        ended_at__isnull=False,
        started_at__date__gte=last_7_days,
        user=request.user
    )
    
    # Totais gerais
    totals = recent_sessions.aggregate(
        total_sessions=Count('id'),
        total_in=Sum('total_in'),
        total_out=Sum('total_out')
    )
    
    # Calcular saldo
    totals['balance'] = (totals['total_in'] or 0) - (totals['total_out'] or 0)
    
    # Dados por dia (últimos 7 dias)
    daily_data = []
    weekdays_pt = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    
    for i in range(7):
        date = datetime.now().date() - timedelta(days=i)
        day_sessions = recent_sessions.filter(started_at__date=date)
        daily_totals = day_sessions.aggregate(
            in_count=Sum('total_in'),
            out_count=Sum('total_out'),
            session_count=Count('id')
        )
        
        weekday_pt = weekdays_pt[date.weekday()]
        
        daily_data.append({
            'date': date.strftime('%d/%m'),
            'full_date': date.strftime('%Y-%m-%d'),
            'weekday': weekday_pt,
            'in': daily_totals['in_count'] or 0,
            'out': daily_totals['out_count'] or 0,
            'balance': (daily_totals['in_count'] or 0) - (daily_totals['out_count'] or 0),
            'sessions': daily_totals['session_count'] or 0
        })
    
    daily_data.reverse()  # Ordem cronológica

    context = {
        "sessions": sessions_page,
        "camera_filter": camera_filter,
        "date_filter": date_filter,
        "animal_filter": animal_filter,
        "animal_types": animal_types,
        "user_cameras": user_cameras,
        "totals": totals,
        "daily_data": daily_data,
    }

    return render(request, "historico/historico.html", context)


@login_required
def log_detail(request, log_id):
    """
    Detalhes de uma sessão de contagem específica
    """
    from django.shortcuts import get_object_or_404
    import json
    import os
    from django.conf import settings
    
    session = get_object_or_404(CountingSession, id=log_id)
    
    # Tentar carregar log de eventos se existir
    events = []
    if session.log_file_path:
        log_path = os.path.join(settings.MEDIA_ROOT, session.log_file_path)
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r') as f:
                    log_data = json.load(f)
                    events = log_data.get('events', [])
            except Exception as e:
                logger.error(f"Erro ao carregar log {log_path}: {e}")
    
    return render(request, "historico/log_detail.html", {
        "session": session,
        "events": events
    })
