import time
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from pathlib import Path
from django.contrib.staticfiles import finders
# import cv2  # Comentado temporariamente
from django.http import JsonResponse
from pathlib import Path
from django.conf import settings
# from .services.contador.manager import counter_manager  # Comentado temporariamente
# from .services.contador.config import CounterConfig  # Comentado temporariamente
from django.conf import settings


def live_page(request):
    from apps.cameras.models import Camera
    cameras = Camera.objects.filter(is_active=True)
    return render(request, "video_ao_vivo/index.html", {"cameras": cameras})


@csrf_exempt
@require_http_methods(["POST", "GET"])
def api_start(request):
    camera_id = request.GET.get('camera_id') or request.POST.get('camera_id')
    if not camera_id:
        return JsonResponse({"ok": False, "error": "ID da câmera não fornecido"}, status=400)
    
    try:
        from apps.cameras.models import Camera
        camera = Camera.objects.get(id=camera_id)
        
        # Usar URL da câmera
        video_source = camera.rtsp_url or camera.stream_url
        if not video_source:
            return JsonResponse({"ok": False, "error": "Câmera sem URL configurada"}, status=400)
        
        # Usar modelo da câmera ou padrão
        if camera.model_config and camera.model_config.model_file:
            model_path = camera.model_config.model_file.path
        else:
            base_dir = Path(settings.BASE_DIR)
            model_path = base_dir / "models" / "yolov8n.pt"
        
        if not Path(model_path).exists():
            return JsonResponse({"ok": False, "error": f"Modelo não encontrado: {model_path}"}, status=400)
        
        # Detecta GPU/CPU
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Usando device: {device}")
        print(f"Câmera: {camera.name} - {video_source}")
        print(f"Modelo: {model_path}")
        
        cfg = CounterConfig(
            model_path=model_path,
            line_y_norm=0.7,
            conf_thres=0.25,
            resize_scale=1.0,
            device=device,
        )
        
        counter_manager.start(video_source, cfg)
        return JsonResponse({
            "ok": True,
            "camera_name": camera.name,
            "video_source": str(video_source),
            "model_path": str(model_path),
            "device": device
        })
        
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)



@csrf_exempt
@require_http_methods(["POST", "GET"])
def api_pause(request):
    counter_manager.pause()
    return JsonResponse({"ok": True})


@csrf_exempt
@require_http_methods(["POST", "GET"])
def api_resume(request):
    counter_manager.resume()
    return JsonResponse({"ok": True})


@csrf_exempt
@require_http_methods(["POST", "GET"])
def api_stop(request):
    counter_manager.stop()
    return JsonResponse({"ok": True})


def api_status(request):
    return JsonResponse(counter_manager.status())


def stream_mjpeg(request):
    def gen():
        while True:
            jpg = counter_manager.get_latest_jpeg()
            if jpg:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n")
            else:
                time.sleep(0.05)

    return StreamingHttpResponse(
        gen(),
        content_type="multipart/x-mixed-replace; boundary=frame"
    )

def api_video_meta(request):
    base_dir = Path(settings.BASE_DIR)
    static_video = base_dir / "static" / "videos" / "cattlecount.mp4"

    cap = cv2.VideoCapture(str(static_video))
    if not cap.isOpened():
        return JsonResponse({"ok": False, "error": "Não abriu vídeo"}, status=400)

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
    cap.release()

    return JsonResponse({"ok": True, "width": w, "height": h, "fps": fps})

import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["POST"])
def api_set_line(request):
    payload = json.loads(request.body.decode("utf-8") or "{}")
    y = float(payload.get("line_y_norm", 0.5))

    # clamp 0..1
    y = max(0.0, min(1.0, y))

    counter_manager.set_line_y_norm(y)
    return JsonResponse({"ok": True, "line_y_norm": y})

@require_http_methods(["GET"])
def api_snapshot(request):
    """Retorna um snapshot da câmera selecionada"""
    camera_id = request.GET.get('camera_id')
    if not camera_id:
        return JsonResponse({"ok": False, "error": "ID da câmera não fornecido"}, status=400)
    
    try:
        from apps.cameras.models import Camera
        camera = Camera.objects.get(id=camera_id)
        
        # Usar URL da câmera (RTSP ou stream)
        video_url = camera.rtsp_url or camera.stream_url
        if not video_url:
            return JsonResponse({"ok": False, "error": "Câmera sem URL configurada"}, status=400)
        
        cap = cv2.VideoCapture(video_url)
        if not cap.isOpened():
            return JsonResponse({"ok": False, "error": "Não foi possível conectar à câmera"}, status=400)
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return JsonResponse({"ok": False, "error": "Erro ao capturar frame da câmera"}, status=400)
        
        _, buffer = cv2.imencode('.jpg', frame)
        
        from django.http import HttpResponse
        return HttpResponse(buffer.tobytes(), content_type="image/jpeg")
        
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@require_http_methods(["GET"])
def api_events(request):
    after = int(request.GET.get("after", "0"))
    events = counter_manager.get_events_after(after)
    return JsonResponse({"ok": True, "events": events})