import socket
import sys
from urllib.parse import urlparse

def test_rtsp_connectivity(url):
    print(f"Testando conectividade: {url}")
    
    try:
        # Parse da URL RTSP
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 554  # porta padrão RTSP
        
        print(f"Host: {host}")
        print(f"Porta: {port}")
        
        # Teste de conectividade TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # timeout de 10 segundos
        
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print("✅ Conectividade TCP OK - Porta acessível")
            return True
        else:
            print(f"❌ Erro de conectividade TCP - Código: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    url = "rtsp://100.112.146.92:8554/cow1"
    test_rtsp_connectivity(url)