"""
Django settings for config project.
"""

from pathlib import Path
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# =====================================================
# BASE DIR
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Permite importar apps.*
sys.path.append(str(BASE_DIR / "apps"))

# =====================================================
# SEGURANÇA
# =====================================================

SECRET_KEY = "django-insecure-mm6!knxfr)t5*dlx1bh$yym9&rbekztoxgkat40yfns6(%+e5q"
DEBUG = True
ALLOWED_HOSTS = [
    "oink.tarslabs.io",
    "100.112.197.98",
    "82.25.75.199",
    '100.112.146.92',
    "localhost",
    "127.0.0.1",
    "192.168.0.43",
    "100.93.97.65"
]

# =====================================================
# APLICAÇÕES
# =====================================================

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Apps do projeto
    "apps.usuario",
    "apps.home",
    "apps.video_ao_vivo",
    "apps.cameras",
    "apps.configuracao",
    "apps.historico",
    # Social Auth
    "social_django",
]
# WEBRTC_SERVER_URL = "http://127.0.0.1:8080"
WEBRTC_SERVER_URL = os.getenv('WEBRTC_URL', 'http://localhost:8888')
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_DOMAIN = None
CSRF_COOKIE_DOMAIN = None

# =====================================================
# MIDDLEWARE
# =====================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# =====================================================
# URLS / WSGI
# =====================================================

ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"

# =====================================================
# TEMPLATES
# =====================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
            BASE_DIR / "apps" / "home" / "templates",
            BASE_DIR / "apps" / "video_ao_vivo" / "templates",
            BASE_DIR / "apps" / "usuario" / "templates",
            BASE_DIR / "apps" / "configuracao" / "templates",
            BASE_DIR / "apps" / "historico" / "templates",
            BASE_DIR / "apps" / "cameras" / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Social Auth
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ],
        },
    },
]

# =====================================================
# BANCO DE DADOS
# =====================================================

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", "oink"), 
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
    }
}


# =====================================================
# USUÁRIO CUSTOMIZADO
# =====================================================

# CSRF_TRUSTED_ORIGINS = ["https://oink.tarslabs.io", "http://127.0.0.1:8000"]
CSRF_TRUSTED_ORIGINS = [
    'http://100.112.146.92:5050',
    'http://localhost:5050',
    'http://127.0.0.1:5050',
    'https://oink.tarslabs.io'
]

SESSION_COOKIE_SECURE = False  # True apenas com HTTPS
CSRF_COOKIE_SECURE = False  # True apenas com HTTPS
SECURE_SSL_REDIRECT = False
SECURE_CROSS_ORIGIN_OPENER_POLICY = None

AUTH_USER_MODEL = "usuario.User"

# =====================================================
# AUTENTICAÇÃO
# =====================================================

AUTHENTICATION_BACKENDS = (
    "social_core.backends.google.GoogleOAuth2",
    "django.contrib.auth.backends.ModelBackend",
)

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"

# =====================================================
# GOOGLE OAUTH (Python Social Auth)
# =====================================================

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv("GOOGLE_OAUTH2_KEY")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv("GOOGLE_OAUTH2_SECRET")

# SCOPES CORRETOS (essencial para foto)
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    "openid",
    "email",
    "profile",
]

# Força captura dos dados do perfil (sem salvar em User)
SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = [
    ("picture", "picture"),
    ("name", "name"),
    ("given_name", "given_name"),
    ("family_name", "family_name"),
]

SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.social_auth.associate_by_email",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)

SOCIAL_AUTH_LOGIN_ERROR_URL = "/login/"
SOCIAL_AUTH_RAISE_EXCEPTIONS = False

# Mude para True em Produção e False para localhost para usar o login do google
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False

# =====================================================
# PASSWORD VALIDATORS
# =====================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =====================================================
# I18N / TZ
# =====================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# =====================================================
# STATIC FILES
# =====================================================

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =====================================================
# LOGGING
# =====================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "db": {
            "level": "INFO",
            "class": "apps.historico.handlers.DatabaseLogHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["db", "console"],
            "level": "INFO",
            "propagate": True,
        },
        "apps": {
            "handlers": ["db", "console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

# =====================================================
# CONFIGURAÇÕES PARA THREADING E MULTIPROCESSING
# =====================================================

# Configurações para evitar problemas com threads em produção
import os
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')
os.environ.setdefault('NUMEXPR_NUM_THREADS', '1')
os.environ.setdefault('TORCH_NUM_THREADS', '1')

# =====================================================
# MEDIA
# =====================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
