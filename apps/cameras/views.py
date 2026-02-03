# apps/cameras/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Camera
from .forms import CameraForm


@login_required
def camera_list(request):
    """Lista todas as câmeras do usuário"""
    cameras = Camera.objects.filter(user=request.user)
    return render(request, "configuracao/index.html", {"cameras": cameras})


# views.py
@login_required
def camera_create(request):
    """Cria nova câmera"""
    if request.method == "POST":
        form = CameraForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("cameras:list")
    else:
        form = CameraForm(user=request.user)
    return render(
        request, "cameras/camera_form.html", {"form": form, "is_editing": False}
    )


@login_required
def camera_update(request, pk):
    """Atualiza câmera existente"""
    camera = get_object_or_404(Camera, pk=pk, user=request.user)
    if request.method == "POST":
        form = CameraForm(request.POST, instance=camera, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("cameras:list")
    else:
        form = CameraForm(instance=camera, user=request.user)
    return render(
        request,
        "cameras/camera_form.html",
        {"form": form, "camera": camera, "is_editing": True},
    )


@login_required
def camera_delete(request, pk):
    """Deleta câmera"""
    camera = get_object_or_404(Camera, pk=pk, user=request.user)
    if request.method == "POST":
        camera.delete()
        return redirect("cameras:list")
    return render(request, "cameras/camera_confirm_delete.html", {"camera": camera})


@login_required
def camera_live(request, pk):
    """Visualiza câmera ao vivo via WebRTC ou HTTP"""
    camera = get_object_or_404(Camera, pk=pk, user=request.user)

    # Pega a URL primária da câmera (HTTP tem prioridade)
    camera_url = camera.primary_url

    if not camera_url:
        return render(
            request,
            "cameras/camera_live.html",
            {"camera": camera, "error": "Esta câmera não possui URL configurada"},
        )

    return render(
        request, "cameras/camera_live.html", {"camera": camera, "rtsp_url": camera_url}
    )
