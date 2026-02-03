import time
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from pathlib import Path
from django.contrib.staticfiles import finders
import cv2
from django.http import JsonResponse
from pathlib import Path
from django.conf import settings
from .services.contador.manager import counter_manager
from .services.contador.config import CounterConfig
from django.conf import settings


def live_page(request):
    from apps.cameras.models import Camera
    cameras = Camera.objects.filter(is_active=True)
    return render(request, "video_ao_vivo/index.html", {"cameras": cameras})


@csrf_exempt
@require_http_methods(["POST", "GET"])
def api_start(request):
    base_dir = Path(settings.BASE_DIR)
    static_video = base_dir / "static" / "videos" / "cattlecount.mp4"
    model_path = base_dir / "models" / "yolov8n.pt"

    print("BASE_DIR =", base_dir)
    print("VIDEO_PATH =", static_video, "exists?", static_video.exists())
    print("MODEL_PATH =", model_path, "exists?", model_path.exists())

    if not static_video.exists():
        return JsonResponse({"ok": False, "error": f"Video não encontrado: {static_video}"}, status=400)

    if not model_path.exists():
        return JsonResponse({"ok": False, "error": f"Modelo não encontrado: {model_path}"}, status=400)

    # Detecta GPU/CPU
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Usando device: {device}")

    cfg = CounterConfig(
    model_path=model_path,
    line_y_norm=0.7,
    conf_thres=0.25,
    resize_scale=1.0,
    device=device,
)


    counter_manager.start(static_video, cfg)
    return JsonResponse({
    "ok": True,
    "video_path": str(static_video),
    "model_path": str(model_path),
    "device": device
    })



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
    """Retorna um snapshot da câmera para configuração da linha"""
    base_dir = Path(settings.BASE_DIR)
    static_video = base_dir / "static" / "videos" / "cattlecount.mp4"
    
    cap = cv2.VideoCapture(str(static_video))
    if not cap.isOpened():
        return JsonResponse({"ok": False, "error": "Não abriu vídeo"}, status=400)
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return JsonResponse({"ok": False, "error": "Erro ao capturar frame"}, status=400)
    
    _, buffer = cv2.imencode('.jpg', frame)
    
    from django.http import HttpResponse
    return HttpResponse(buffer.tobytes(), content_type="image/jpeg")

@require_http_methods(["GET"])
def api_events(request):
    after = int(request.GET.get("after", "0"))
    events = counter_manager.get_events_after(after)
    return JsonResponse({"ok": True, "events": events})