import cv2
import time

def test_rtsp(url):
    print(f"Testando RTSP: {url}")
    
    cap = cv2.VideoCapture(url)
    
    if not cap.isOpened():
        print("ERRO: Nao foi possivel conectar ao stream RTSP")
        return False
    
    print("OK: Conexao RTSP estabelecida")
    
    # Tentar ler alguns frames
    for i in range(5):
        ret, frame = cap.read()
        if ret:
            h, w = frame.shape[:2]
            print(f"Frame {i+1}: {w}x{h} pixels")
        else:
            print(f"ERRO: Falha ao ler frame {i+1}")
            break
        time.sleep(0.1)
    
    # Informacoes do stream
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    
    print(f"Resolucao: {int(width)}x{int(height)}")
    print(f"FPS: {fps}")
    
    cap.release()
    return True

if __name__ == "__main__":
    rtsp_url = "rtsp://82.25.75.199:8554/1216"
    test_rtsp(rtsp_url)