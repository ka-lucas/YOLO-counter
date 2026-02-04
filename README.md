# Oink Platform 🐷

Plataforma de monitoramento de vídeo inteligente (NVR/VMS) focada em performance e execução em dispositivos de borda (Edge AI), como NVIDIA Jetson Nano.

O sistema transforma câmeras RTSP comuns em um sistema de vigilância e detecção avançado com visualização de baixa latência via WebRTC e detecção inteligente de objetos com IA.

## 🚀 Funcionalidades Principais

- **Streaming em Tempo Real**: Visualização de múltiplas câmeras com latência ultra-baixa usando WebRTC
- **Detecção Inteligente**: Integração com modelos YOLO (V8/V11) para identificar pessoas, veículos e objetos personalizados
- **Contagem de Objetos**: Sistema de contagem em tempo real de objetos detectados por câmera
- **Gestão de Câmeras**: Interface administrativa intuitiva para adicionar e configurar fontes RTSP/HTTP
- **Filtros por Classe**: Filtragem dinâmica de detecções por tipo de objeto
- **Configuração de Modelos**: Suporte a múltiplos modelos YOLO com seleção por câmera
- **Histórico de Eventos**: Sistema de logs e rastreamento de detecções
- **Otimização de Performance**: Servidor robusto contra instabilidades de conexão com reconexão automática
- **Suporte a Múltiplos Usuários**: Autenticação integrada e isolamento de câmeras por usuário
- **API REST**: Endpoints para integração com sistemas externos

## 🛠️ Stack Tecnológico

| Componente | Tecnologia |
|------------|-----------|
| **Backend** | Django 4.2 + Django REST Framework |
| **Streaming** | WebRTC (aiortc + aiohttp) + OpenCV |
| **IA/Visão Computacional** | Ultralytics YOLOv8/v11 |
| **Banco de Dados** | MySQL / MariaDB |
| **Servidor Web** | Gunicorn |
| **Infraestrutura** | Docker & Docker Compose |
| **Hardware Alvo** | NVIDIA Jetson (GPU otimizada) + x86_64 (CPU) |
| **Autenticação** | JWT + Social Auth + OAuth2 |

## 📂 Estrutura do Projeto

```
oink-platform/
├── apps/                      # Aplicações Django (Lógica de negócios)
│   ├── cameras/               # Gestão de dispositivos e configuração
│   │   ├── models.py          # Modelo de Câmera + Classes YOLO
│   │   ├── views.py           # Endpoints da API
│   │   ├── forms.py           # Formulários administrativos
│   │   └── templates/
│   ├── video_ao_vivo/         # Interface de visualização em tempo real
│   │   ├── views.py           # Lógica de streaming e detecção
│   │   ├── services/contador/ # Motor de contagem de objetos
│   │   └── templates/
│   ├── configuracao/          # Configuração de modelos YOLO
│   │   ├── models.py          # Modelo de Configuração
│   │   └── views.py
│   ├── historico/             # Logs de eventos e detecções
│   │   ├── handlers.py        # Event handlers
│   │   └── models.py
│   ├── usuario/               # Autenticação e gerenciamento de usuários
│   ├── home/                  # Dashboard principal
│   └── __init__.py
├── core/                      # Configurações centralizadas
│   ├── settings.py            # Configurações Django
│   ├── urls.py                # Rotas principais
│   ├── wsgi.py                # WSGI para Gunicorn
│   └── asgi.py                # ASGI para async
├── models/                    # Pesos dos modelos YOLO (.pt)
│   ├── yolo11n.pt
│   ├── yolov8n.pt
│   └── ...
├── media/                     # Arquivos de mídia
│   ├── videos/                # Vídeos gravados
│   ├── counting_logs/         # Logs JSON de contagem
│   └── models/
├── scripts/                   # Utilitários e inicialização
│   ├── create_superuser.py    # Script de criação de admin
│   └── seed_user.py
├── static/                    # Arquivos estáticos (CSS, JS)
├── staticfiles/               # Arquivos estáticos compilados
├── webrtc_server.py           # Servidor WebRTC standalone
├── docker-compose.yml         # Orquestração para Jetson (GPU)
├── docker-compose.x86.yml     # Orquestração para x86_64 (CPU)
├── Dockerfile                 # Imagem para ARM/Jetson
├── Dockerfile.cpu             # Imagem para x86_64
├── Makefile                   # Automação de build/run
└── manage.py                  # CLI do Django
```

## 🚀 Como Executar

### Pré-requisitos

- **Docker** e **Docker Compose** instalados
- **(Opcional) Runtime NVIDIA Container** para GPU (Jetson/NVIDIA)
- Mínimo 2GB de RAM livre
- Câmeras RTSP acessíveis

### Instalação Rápida (usando Makefile)

```bash
# Clone o repositório
git clone <url-do-repo>
cd oink-platform

# Construa os containers (auto-detecta arquitetura)
make build

# Inicie os serviços
make run

# Verifique os logs
make logs
```

### Instalação Manual

```bash
# Configure o arquivo .env (copie de exemplo se existir)
cp .env.example .env  # ou edite manualmente

# Escolha a composição correta:
# Para NVIDIA Jetson (GPU):
docker-compose -f docker-compose.yml up -d --build

# Ou para x86_64 (CPU):
docker-compose -f docker-compose.x86.yml up -d --build

# Execute migrações
docker-compose exec app python manage.py migrate

# Crie superusuário (ou use script)
docker-compose exec app python scripts/create_superuser.py
```

## 🌐 Acesso à Aplicação

| Serviço | URL | Descrição |
|---------|-----|----------|
| **Web UI** | `http://localhost:5050` | Painel de visualização e gerenciamento |
| **Admin Django** | `http://localhost:5050/admin` | Painel administrativo |
| **API REST** | `http://localhost:5050/api` | Endpoints da API |
| **WebRTC** | `ws://localhost:8888` | Streaming de vídeo em tempo real |

**Credenciais Padrão:**
- Usuário: `gaspar`
- Senha: Definida durante `create_superuser.py`

## ⚙️ Configuração

### Variáveis de Ambiente (.env)

```env
# Banco de dados
DB_ENGINE=django.db.backends.mysql
DB_NAME=oink_db
DB_USER=root
DB_PASSWORD=senha_db
DB_HOST=mysql
DB_PORT=3306

# Segurança
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.100

# Autenticação Social (opcional)
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=...
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=...

# Storage (MinIO opcional)
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
```

### Adicionar Câmera

1. Acesse o painel admin em `/admin`
2. Navegue para **Cameras**
3. Clique em **Add Camera**
4. Preencha:
   - **Nome**: Identificação da câmera
   - **URL RTSP**: `rtsp://192.168.1.100:554/stream`
   - **Local**: Localização física
   - **Modelo**: Selecione modelo YOLO configurado
5. Salve e ative

### Configurar Modelo YOLO

1. Acesse `/admin/configuracao/modelconfiguration/`
2. Crie nova configuração:
   - **Nome**: Ex: "YOLOv8 Pessoas"
   - **Arquivo .pt**: Upload do modelo
   - **Classes Alvo**: Selecione as classes a detectar (person, car, etc)
3. Associe à câmera desejada

## 📊 Endpoints da API

### Câmeras
```
GET    /api/cameras/              # Listar câmeras do usuário
POST   /api/cameras/              # Criar nova câmera
GET    /api/cameras/<id>/         # Detalhes de câmera
PATCH  /api/cameras/<id>/         # Atualizar câmera
DELETE /api/cameras/<id>/         # Deletar câmera
```

### Detecções
```
GET    /api/detections/           # Listar detecções
GET    /api/detections/stats/     # Estatísticas por câmera
```

### Streaming
```
GET    /api/start?camera_id=<id>  # Inicia detecção e streaming
POST   /api/start                 # (alternativa POST)
```

## 🔍 Monitoramento e Logs

```bash
# Logs em tempo real
docker-compose logs -f app

# Logs do WebRTC
docker-compose logs -f webrtc

# Logs de um container específico
docker logs -f oink_plataform

# Acesse as estatísticas
docker stats
```

## 🛠️ Manutenção

### Parar Serviços
```bash
make stop
# ou
docker-compose down
```

### Reiniciar Serviços
```bash
docker-compose restart app
docker-compose restart webrtc
```

### Limpar Banco de Dados
```bash
docker-compose down -v  # Remove containers e volumes
make clean              # Usando Makefile
```

### Atualizar Código
```bash
git pull origin main
make build
make run
```

## 📈 Performance e Otimização

### Para Jetson Nano
- GPU ativada automaticamente via runtime `nvidia`
- Limite de memória: 3GB (ajustável em docker-compose.yml)
- Recomendado: Usar modelo YOLOv8n (nano) ou v11n

### Para x86_64
- Execução em CPU
- Escale workers do Gunicorn: altere `--workers 4` em docker-compose.x86.yml
- Use `--threads 8` para melhor throughput

## 🐛 Troubleshooting

| Problema | Solução |
|----------|---------|
| **Câmera não conecta** | Verifique URL RTSP, firewall, credenciais |
| **Latência alta** | Reduz resolução, verifica bandwidth da rede |
| **Out of Memory** | Limita workers, reduz batch_size, escolhe modelo menor |
| **Detecção lenta** | Verifique modelo (nano é mais rápido), aumente GPU usage |
| **Container não inicia** | Verifica `.env`, logs, disponibilidade de porta 5050 |

## 📝 Desenvolvimento

### Dependências Principais
```
Django==4.2.11
djangorestframework==3.14.0
opencv-python-headless==4.8.1.78
ultralytics==8.0.0
gunicorn==21.2.0
mysqlclient==2.2.0
```

### Instalação Local
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```

### Executar Testes
```bash
python manage.py test
# ou
docker-compose exec app python manage.py test
```

## 🔐 Segurança

- Altere `SECRET_KEY` em produção
- Configure `DEBUG = False`
- Use HTTPS com reverse proxy (nginx)
- Implemente rate limiting
- Validar todas as URLs RTSP
- Usar firewall e VPN para acesso remoto

## 📄 Licença

Proprietário - Tarslabs

## 👥 Suporte

Para dúvidas ou problemas:
1. Verifique logs: `make logs`
2. Consulte troubleshooting acima
3. Abra issue no repositório

---

**Desenvolvido com foco em eficiência, robustez e performance em dispositivos Edge.** 🚀
