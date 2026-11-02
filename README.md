# Yolo Counter OS

Aplicacao Django para contagem inteligente em video, com gerenciamento de cameras, modelos YOLO, historico de sessoes e operacao em tempo real.

## Visao geral

O projeto inclui:

- dashboard web com metricas operacionais
- modulo de video ao vivo para iniciar, pausar, retomar e encerrar contagens
- cadastro de cameras RTSP ou HTTP/MJPEG por usuario
- configuracao e ativacao de modelos `.pt`
- historico de sessoes de contagem
- autenticacao por email e opcionalmente Google OAuth

## Stack

| Camada | Tecnologia |
| --- | --- |
| Backend | Django 4.2 |
| API/Auth | Django auth + Python Social Auth |
| Banco | SQLite ou MySQL/MariaDB |
| IA | Ultralytics YOLO |
| Video | OpenCV + servicos de contagem |
| Deploy | Docker / Docker Compose |
| Estaticos | WhiteNoise |

## 📂 Estrutura do Projeto

```
yolo_counter-platform/
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
│   └── seed_demo.py           # Dados fictícios para demo
├── create_superuser.py        # Cria admin a partir do .env
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
cd yolo_counter_platform

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
cp .env.example .env  # e troque SECRET_KEY e a senha do admin

# Escolha a composição correta:
# Para NVIDIA Jetson (GPU):
docker-compose -f docker-compose.yml up -d --build

# Ou para x86_64 (CPU):
docker-compose -f docker-compose.x86.yml up -d --build

# Execute migrações
docker-compose exec app python manage.py migrate

# Crie superusuário (ou use script)
docker-compose exec app python create_superuser.py
```

## 🌐 Acesso à Aplicação

| Serviço | URL | Descrição |
|---------|-----|----------|
| **Web UI** | `http://localhost:5050` | Painel de visualização e gerenciamento |
| **Admin Django** | `http://localhost:5050/admin` | Painel administrativo |
| **API REST** | `http://localhost:5050/api` | Endpoints da API |
| **WebRTC** | `ws://localhost:8888` | Streaming de vídeo em tempo real |

**Credenciais:** definidas por `DJANGO_SUPERUSER_EMAIL` e `DJANGO_SUPERUSER_PASSWORD` no `.env`.

## ⚙️ Configuração

### Variáveis de Ambiente (.env)

```env
DB_ENGINE=
DB_NAME=
DB_USER=root
DB_PASSWORD=senha_db
DB_HOST=mysql
DB_PORT=3306

# Segurança
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:5050,http://127.0.0.1:5050

# Admin (create_superuser.py)
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=...

# Autenticação Social (opcional)
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=...
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=...

# Storage (MinIO opcional)
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
```

### Variaveis usadas

- `DB_ENGINE`: default `django.db.backends.sqlite3`
- `DB_NAME`: default `oink`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `GOOGLE_OAUTH2_KEY`
- `GOOGLE_OAUTH2_SECRET`
- `WEBRTC_URL`: default `http://localhost:8888`

## Execucao local

### 1. Criar e ativar o ambiente virtual

Windows:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

Linux/macOS:

```bash
python -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar o `.env`

Copie `.env_example` para `.env` e preencha os valores.

### 4. Rodar migracoes

```bash
python manage.py migrate
```

### 5. Criar usuario admin

O script usa:

- `DJANGO_SUPERUSER_EMAIL`
- `DJANGO_SUPERUSER_PASSWORD`

Exemplo:

```powershell
$env:DJANGO_SUPERUSER_EMAIL="admin@local.test"
$env:DJANGO_SUPERUSER_PASSWORD="SenhaForte123!"
python create_superuser.py
```

### 6. Iniciar a aplicacao

```bash
python manage.py runserver
```

Acesso local:

- Web: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`
- Login: `http://127.0.0.1:8000/login/`

## Execucao com Docker

### GPU / Jetson

```bash
docker-compose -f docker-compose.yml up -d --build
```

### CPU / x86

```bash
docker-compose -f docker-compose.x86.yml up -d --build
```

Depois:

```bash
docker-compose exec app python manage.py migrate
```

## Autenticacao

O projeto usa:

- login por email e senha
- logout Django padrao
- login social com Google em `/oauth/`

Configuracoes relevantes:

- `AUTH_USER_MODEL = "usuario.User"`
- backend `social_core.backends.google.GoogleOAuth2`

## Cameras e sessoes

Cada camera:

- pertence a um usuario
- pode usar `rtsp_url` ou `stream_url`
- possui classe de deteccao unica
- pode ser associada a um modelo

Modelos principais:

- `apps.cameras.models.Camera`
- `apps.video_ao_vivo.models.CountingSession`
- `apps.configuracao.models.ModelConfiguration`

## Desenvolvimento

Comandos uteis:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py test
python manage.py check
```

## Observacoes de seguranca

- Altere `SECRET_KEY` em produção
- Configure `DEBUG = False`
- Use HTTPS com reverse proxy (nginx)
- Implemente rate limiting
- Validar todas as URLs RTSP
- Usar firewall e VPN para acesso remoto

## 📌 Origem

Projeto pessoal, reimplementado a partir da minha experiência com contagem por visão computacional. Usa apenas os pesos oficiais da Ultralytics e vídeos públicos de licença aberta (ex.: Pexels).

## 📄 Licença

MIT — veja [LICENSE](LICENSE).

## 👥 Suporte

Para dúvidas ou problemas:
1. Verifique logs: `make logs`
2. Consulte troubleshooting acima
3. Abra issue no repositório

---

**Desenvolvido com foco em eficiência, robustez e performance em dispositivos Edge.** 🚀
