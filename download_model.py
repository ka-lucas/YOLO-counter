import requests
import os
from pathlib import Path

def download_yolo_model():
    """Baixa modelo YOLOv8n oficial do Ultralytics"""
    
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    model_url = "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt"
    model_path = models_dir / "yolov8n_official.pt"
    
    if model_path.exists():
        print(f"Modelo já existe: {model_path}")
        return str(model_path)
    
    print(f"Baixando modelo de {model_url}...")
    
    try:
        response = requests.get(model_url, stream=True)
        response.raise_for_status()
        
        with open(model_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Modelo baixado: {model_path}")
        return str(model_path)
        
    except Exception as e:
        print(f"Erro ao baixar modelo: {e}")
        return None

if __name__ == "__main__":
    download_yolo_model()