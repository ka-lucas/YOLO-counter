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

## Estrutura principal

```text
yolo-counter/
|- apps/
|  |- cameras/
|  |- configuracao/
|  |- historico/
|  |- home/
|  |- usuario/
|  |- video_ao_vivo/
|- core/
|- media/
|- models/
|- scripts/
|- static/
|- staticfiles/
|- .env_example
|- add_camera.py
|- create_superuser.py
|- docker-compose.yml
|- docker-compose.x86.yml
|- download_model.py
|- manage.py
|- requirements.txt
|- rtsp_proxy.py
|- webrtc_server.py
```

## Modulos

### Dashboard

- resumo de entradas, saidas e total detectado
- grafico de evolucao
- fluxo por minuto
- alertas operacionais
- status simplificado das cameras

### Video ao vivo

Rotas em `/video-ao-vivo/`:

```text
GET  /video-ao-vivo/
GET  /video-ao-vivo/live/
GET  /video-ao-vivo/api/status/
POST /video-ao-vivo/api/start/
POST /video-ao-vivo/api/pause/
POST /video-ao-vivo/api/resume/
POST /video-ao-vivo/api/stop/
POST /video-ao-vivo/api/line/
GET  /video-ao-vivo/api/events/
GET  /video-ao-vivo/api/chart-data/
GET  /video-ao-vivo/stream/
```

### Configuracao

Em `/configuracoes/`:

- upload e ativacao de modelos `.pt`
- ajuste de confianca
- gerenciamento de cameras
- configuracoes gerais do sistema

### Historico

Em `/historico/`:

- listagem de sessoes finalizadas
- filtros por camera, data e classe
- detalhes de sessao com eventos, quando houver log

## Requisitos

- Python 3.12 recomendado
- pip
- ambiente virtual
- opcionalmente Docker e Docker Compose
- opcionalmente MySQL/MariaDB

## Configuracao de ambiente

Use `.env_example` como base:

```env
DB_ENGINE=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
GOOGLE_OAUTH2_KEY=
GOOGLE_OAUTH2_SECRET=
WEBRTC_URL=
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

- nao versione `.env`
- nao deixe credenciais hardcoded em producao
- ajuste `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` e cookies seguros antes de subir
- mantenha `GOOGLE_OAUTH2_KEY` e `GOOGLE_OAUTH2_SECRET` apenas via ambiente

## Limitacoes atuais

- `api_snapshot` retorna `503` e esta temporariamente desabilitada
- `api_video_meta` retorna `503` e esta temporariamente desabilitada
- a operacao de video depende do ambiente ter OpenCV, YOLO e runtime compativeis

## Troubleshooting

### Push bloqueado por segredo no GitHub

Se o push for bloqueado por Push Protection, editar o arquivo atual nao resolve quando o segredo esta no historico. Nesse caso, a saida correta e criar uma branch nova limpa baseada em `origin/main` e reaplicar apenas o snapshot atual.

### Erro no login Google

Verifique:

- `GOOGLE_OAUTH2_KEY`
- `GOOGLE_OAUTH2_SECRET`
- callback configurada no provider
- `SOCIAL_AUTH_REDIRECT_IS_HTTPS`

### Camera nao inicia contagem

Verifique:

- camera ativa
- `primary_url` configurada
- modelo associado, quando necessario
- dependencias de YOLO/OpenCV instaladas corretamente

## Licenca

Projeto proprietario.
