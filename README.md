# Oink Platform 🐷

Platforma de monitoramento de vídeo inteligente (NVR/VMS) focada em performance e execução em dispositivos de borda (Edge AI), como NVIDIA Jetson Nano.

O sistema transforma câmeras RTSP comuns em um sistema de segurança avançado com visualização de baixa latência via WebRTC e detecção de objetos com IA.

## 🚀 Funcionalidades

-   **Streaming em Tempo Real**: Visualização de câmeras com latência de sub-segundo usando WebRTC.
-   **Detecção de Objetos**: Integração com modelos YOLO (V8/V11) para identificar pessoas, veículos e outros objetos.
-   **Otimização de Rede**: Servidor de streaming robusto contra instabilidades de conexão (reconexão automática, buffer adaptativo).
-   **Gestão de Câmeras**: Interface administrativa para adicionar e configurar fontes RTSP.
-   **Histórico e Gravação**: Sistema de logs e armazenamento de eventos.

## 🛠️ Stack Tecnológico

-   **Backend**: Django (Python) + Django REST Framework.
-   **Streaming**: WebRTC (aiortc + aiohttp) & OpenCV.
-   **IA/Visão Computacional**: Ultralytics YOLOv8/v11.
-   **Banco de Dados**: MySQL.
-   **Infraestrutura**: Docker & Docker Compose.
-   **Hardware Alvo**: Otimizado para NVIDIA Jetson (Runtime `nvidia`).

## 📂 Estrutura do Projeto

```text
oink-platform/
├── apps/               # Aplicações Django (Lógica de negeócios)
│   ├── cameras/        # Gestão de dispositivos e streams
│   ├── video_ao_vivo/  # Interface de visualização
│   ├── historico/      # Logs de eventos
│   └── ...
├── core/               # Configurações do projeto (settings, urls)
├── models/             # Pesos dos modelos YOLO (.pt)
├── webrtc_server.py    # Servidor standalone de streaming WebRTC
├── docker-compose.yml  # Orquestração dos containers (App + WebRTC)
└── manage.py           # CLI do Django
```

## ⚡ Como Executar

### Pré-requisitos
-   Docker e Docker Compose instalados.
-   Runtime NVIDIA Container (se rodando em Jetson/GPU).

### Passos

1.  **Clone o repositório:**
    ```bash
    git clone <url-do-repo>
    cd oink-platform
    ```

2.  **Configure o ambiente:**
    Crie um arquivo `.env` na raiz (baseie-se nas variáveis usadas no `settings.py` ou solicite um exemplo).

3.  **Inicie os containers:**
    ```bash
    docker-compose up -d --build
    ```

4.  **Acesse a aplicação:**
    -   Painel Web: `http://localhost:5050` (ou IP do dispositivo).
    -   API/Streaming: `http://localhost:8888` (porta interna do WebRTC).

## 🔧 Manutenção

-   **Logs do WebRTC**: `docker logs -f oink_webrtc`
-   **Logs do Django**: `docker logs -f oink_plataform`

---
*Desenvolvido com foco em eficiência e robustez.*
