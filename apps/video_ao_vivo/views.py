import time
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from pathlib import Path
from django.contrib.staticfiles import finders
from django.conf import settings


def live_page(request):
    from apps.cameras.models import Camera
    cameras = Camera.objects.filter(is_active=True, user=request.user)
    # Obter lista distinta de detection_class_name (exclui vazios)
    animal_types = (
        Camera.objects.filter(is_active=True, user=request.user)
        .exclude(detection_class_name__exact='')
        .values_list('detection_class_name', flat=True)
        .distinct()
    )
    return render(request, "video_ao_vivo/index.html", {"cameras": cameras, "animal_types": animal_types})


@csrf_exempt
@require_http_methods(["POST", "GET"])
def api_start(request):
    camera_id = request.GET.get('camera_id') or request.POST.get('camera_id')
    
    if not camera_id:
        return JsonResponse({"ok": False, "error": "camera_id é obrigatório"}, status=400)
    
    try:
        from apps.cameras.models import Camera
        camera = Camera.objects.get(id=camera_id, is_active=True, user=request.user)
    except Camera.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Câmera não encontrada"}, status=404)
    
    if not camera.primary_url:
        return JsonResponse({"ok": False, "error": "Câmera sem URL configurada"}, status=400)
    
    # Importar aqui para evitar problemas de import circular
    try:
        from .services.contador.manager import counter_manager
        from .services.contador.config import CounterConfig
        
        # Detecta GPU/CPU
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Criar config básico (modelo será definido pelo manager)
        config = CounterConfig(
            model_path="",  # Será sobrescrito
            conf_thres=0.25,
            resize_scale=1.0,
            device=device,
            line_y_norm=0.5  # Valor padrão, será atualizado pelo set_line
        )
        
        counter_manager.start(camera, request.user, config)
        
        return JsonResponse({
            "ok": True,
            "camera_id": camera_id,
            "camera_name": camera.name,
            "camera_url": camera.primary_url,
            "device": device,
            "message": "Contador iniciado com sucesso"
        })
        
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Erro ao iniciar: {str(e)}"}, status=500)


@csrf_exempt
@require_http_methods(["POST", "GET"])
def api_pause(request):
    try:
        from .services.contador.manager import counter_manager
        counter_manager.pause()
        return JsonResponse({"ok": True, "message": "Contagem pausada"})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST", "GET"])
def api_resume(request):
    try:
        from .services.contador.manager import counter_manager
        counter_manager.resume()
        return JsonResponse({"ok": True, "message": "Contagem retomada"})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST", "GET"])
def api_stop(request):
    try:
        import json
        from .models import CountingSession
        from .services.contador.manager import counter_manager
        
        counter_manager.stop()
        
        # Se for POST com dados JSON, salvar informações adicionais
        if request.method == 'POST' and request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                
                # Obter a sessão de contagem ativa
                # A sessão é criada quando o contador inicia
                # Procurar pela sessão mais recente sem ended_at
                session = CountingSession.objects.filter(ended_at__isnull=True).order_by('-started_at').first()
                
                if session:
                    # Atualizar com as informações adicionais
                    session.animal_type = data.get('animal_type')
                    session.batch_number = data.get('batch_number')
                    session.recipient = data.get('recipient')
                    session.recipient = data.get('recipient')
                    session.additional_notes = data.get('additional_notes')
                    session.ended_at = timezone.now()
                    session.save()
                    
            except json.JSONDecodeError:
                pass  # Se não for JSON válido, apenas continua
        
        return JsonResponse({"ok": True, "message": "Contagem parada"})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


def api_status(request):
    try:
        from .services.contador.manager import counter_manager
        return JsonResponse(counter_manager.status())
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


def stream_mjpeg(request):
    """Stream MJPEG do contador ativo"""
    def generate():
        from .services.contador.manager import counter_manager
        print("Stream MJPEG iniciado")
        
        while True:
            jpeg_data = counter_manager.get_latest_jpeg()
            if jpeg_data:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg_data + b'\r\n')
            else:
                # Frame vazio se não houver dados
                import cv2
                import numpy as np
                blank = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(blank, 'Contador nao iniciado', (150, 220), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(blank, 'Inicie a contagem primeiro', (120, 260), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
                _, buffer = cv2.imencode('.jpg', blank)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.033)  # ~30 FPS
    
    return StreamingHttpResponse(generate(), content_type='multipart/x-mixed-replace; boundary=frame')


def api_video_meta(request):
    return JsonResponse({"ok": False, "error": "Funcionalidade temporariamente desabilitada"}, status=503)


@require_http_methods(["GET"])
def api_snapshot(request):
    return JsonResponse({"ok": False, "error": "Funcionalidade temporariamente desabilitada"}, status=503)


@csrf_exempt
@require_http_methods(["POST"])
def api_set_line(request):
    try:
        import json
        from .services.contador.manager import counter_manager
        
        payload = json.loads(request.body.decode("utf-8") or "{}")
        y = float(payload.get("line_y_norm", 0.5))
        
        # clamp 0..1
        y = max(0.0, min(1.0, y))
        
        counter_manager.set_line_y_norm(y)
        return JsonResponse({"ok": True, "line_y_norm": y})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@require_http_methods(["GET"])
def api_events(request):
    try:
        from .services.contador.manager import counter_manager
        after = int(request.GET.get("after", "0"))
        events = counter_manager.get_events_after(after)
        return JsonResponse({"ok": True, "events": events})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@require_http_methods(["GET"])
def api_chart_data(request):
    """Dados para gráficos em tempo real"""
    try:
        from datetime import datetime, timedelta
        from .models import CountingSession
        from django.db.models import Sum
        import json
        
        # Debug: verificar sessões no banco
        all_sessions = CountingSession.objects.all().order_by('-started_at')[:5]
        debug_sessions = []
        for s in all_sessions:
            debug_sessions.append({
                'id': s.id,
                'started_at': s.started_at.isoformat(),
                'ended_at': s.ended_at.isoformat() if s.ended_at else None,
                'total_in': s.total_in,
                'total_out': s.total_out
            })
        
        # Buscar dados dos últimos 7 dias (igual ao histórico)
        from django.db.models import Sum
        from django.utils import timezone
        
        daily_data = []
        for i in range(7):
            day = timezone.now().date() - timedelta(days=6-i)
            
            day_sessions = CountingSession.objects.filter(
                started_at__date=day,
                ended_at__isnull=False
            )
            
            day_totals = day_sessions.aggregate(
                in_count=Sum('total_in'),
                out_count=Sum('total_out')
            )
            
            daily_data.append({
                'date': day.strftime('%d/%m'),
                'weekday': day.strftime('%a'),
                'in': day_totals['in_count'] or 0,
                'out': day_totals['out_count'] or 0,
                'balance': (day_totals['in_count'] or 0) - (day_totals['out_count'] or 0)
            })
        
        # Converter para formato horário para compatibilidade
        hourly_data = []
        for day in daily_data:
            hourly_data.append({
                'hour': day['weekday'],
                'in': day['in'],
                'out': day['out']
            })
        
        # Dados por minuto da sessão ativa
        minute_data = [0] * 10
        active_session = CountingSession.objects.filter(ended_at__isnull=True).first()
        
        if active_session and active_session.log_file_path:
            import os
            from django.conf import settings
            
            try:
                log_path = os.path.join(settings.MEDIA_ROOT, active_session.log_file_path)
                if os.path.exists(log_path):
                    with open(log_path, 'r') as f:
                        log_data = json.load(f)
                        events = log_data.get('events', [])
                    
                    now = datetime.now()
                    for i in range(10):
                        minute_start = now.replace(second=0, microsecond=0) - timedelta(minutes=i)
                        minute_end = minute_start + timedelta(minutes=1)
                        
                        minute_count = 0
                        for event in events:
                            try:
                                event_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                                if minute_start <= event_time < minute_end:
                                    minute_count += 1
                            except:
                                continue
                        
                        minute_data[9-i] = minute_count
            except Exception as e:
                print(f"Erro ao processar log: {e}")
        
        # Se não há dados nas últimas 24h, manter zeros
        total_data = sum(h['in'] + h['out'] for h in hourly_data)
        
        return JsonResponse({
            "ok": True,
            "hourly_data": hourly_data,
            "minute_data": minute_data,
            "debug": {
                "total_sessions": CountingSession.objects.count(),
                "recent_sessions": recent_sessions.count(),
                "active_sessions": CountingSession.objects.filter(ended_at__isnull=True).count(),
                "sample_sessions": debug_sessions
            }
        })
        
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
