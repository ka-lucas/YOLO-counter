import os
import django
import sys

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.cameras.models import Camera

def add_mjpeg_camera():
    url = "http://216.107.197.101:8086/mjpg/video.mjpg"
    
    # Verificar se já existe
    existing = Camera.objects.filter(stream_url=url).first()
    if existing:
        print(f"Camera já existe: {existing.name}")
        return existing
    
    # Criar nova câmera
    camera = Camera.objects.create(
        name="Câmera MJPEG Externa",
        stream_url=url,
        location="Externa",
        is_active=True
    )
    
    print(f"Câmera adicionada: {camera.name} (ID: {camera.id})")
    return camera

if __name__ == "__main__":
    add_mjpeg_camera()