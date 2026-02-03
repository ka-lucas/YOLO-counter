import cv2
import sys

def test_rtsp_camera(url):
    print(f"Testando câmera: {url}")
    
    try:
        cap = cv2.VideoCapture(url)
        
        if not cap.isOpened():
            print("❌ Erro: Não foi possível conectar à câmera")
            return False
        
        # Tentar ler um frame
        ret, frame = cap.read()
        
        if not ret:
            print("❌ Erro: Não foi possível ler frame da câmera")
            cap.release()
            return False
        
        # Obter informações do stream
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"✅ Câmera funcionando!")
        print(f"   Resolução: {width}x{height}")
        print(f"   FPS: {fps}")
        print(f"   Frame shape: {frame.shape}")
        
        cap.release()
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    url = "rtsp://100.112.146.92:8554/cow1"
    test_rtsp_camera(url)