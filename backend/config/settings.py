# Calculadora RSC-TAE de livre acesso — derivada do ProRSC-TAE (Software Público Brasileiro).
# Licenciado sob a GNU General Public License v2.0 ou posterior (GPL-2.0-or-later).
"""Configurações do Django.

Tudo que muda entre ambientes vem de variáveis de ambiente (arquivo ``.env`` em
desenvolvimento, ``EnvironmentFile`` do systemd em produção).
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _lista(nome: str, padrao: str = "") -> list[str]:
    return [v.strip() for v in os.environ.get(nome, padrao).split(",") if v.strip()]


SECRET_KEY = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")
DEBUG = os.environ.get("DEBUG", "0") == "1"
ALLOWED_HOSTS = _lista("ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = _lista("CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # terceiros
    "rest_framework",
    "corsheaders",
    # do projeto
    "accounts",
    "rsc",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # antes de CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ─── Banco: SQLite ───────────────────────────────────────────────────────────
# O Django já liga as chaves estrangeiras do SQLite; aqui ligamos também o modo WAL.
SQLITE_PATH = Path(os.environ.get("SQLITE_PATH", BASE_DIR / "data" / "prorsc.db"))
SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)  # o SQLite cria o arquivo, não a pasta

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": SQLITE_PATH,
        "OPTIONS": {"init_command": "PRAGMA journal_mode=WAL;"},
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Model de usuário próprio, ligado à tabela "users" do schema original.
AUTH_USER_MODEL = "accounts.Usuario"
BCRYPT_ROUNDS = int(os.environ.get("BCRYPT_ROUNDS", "12"))

# ─── Idioma e fuso ───────────────────────────────────────────────────────────
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True  # grava em UTC; converte para TIME_ZONE ao exibir

# ─── Publicação em subpasta (ex.: https://exemplo.com.br/prorsc_django/) ─────
# O Apache repassa "/prorsc_django/admin/..." como "/admin/..." para o Gunicorn. Com o
# FORCE_SCRIPT_NAME, o Django volta a pôr o prefixo nos links e redirecionamentos que gera
# (login do Admin, reverse(), STATIC_URL relativo). Vazio = aplicação na raiz do domínio.
FORCE_SCRIPT_NAME = os.environ.get("FORCE_SCRIPT_NAME") or None
if FORCE_SCRIPT_NAME:
    # Cookies do Admin restritos à subpasta: não se misturam com outros sistemas do domínio.
    SESSION_COOKIE_PATH = CSRF_COOKIE_PATH = f"{FORCE_SCRIPT_NAME}/"

# ─── Arquivos estáticos (CSS/JS do Django Admin) ─────────────────────────────
# Relativo: o Django prefixa com o FORCE_SCRIPT_NAME (vira "/prorsc_django/static/" na subpasta).
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Rotas sem barra final, como no restante da API (/api/v1/rsc e não /api/v1/rsc/).
APPEND_SLASH = False

# ─── Django REST Framework ───────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["core.autenticacao.JWTAutenticacao"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "core.excecoes.tratar_excecao",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.environ.get("JWT_TTL_MINUTOS", "480"))),
    "SIGNING_KEY": os.environ.get("JWT_SECRET", "troque-este-segredo-jwt-em-producao"),
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_CLAIM": "sub",
    "UPDATE_LAST_LOGIN": False,
}

HASHIDS_SALT = os.environ.get("HASHIDS_SALT", "troque-este-salt")

CORS_ALLOWED_ORIGINS = _lista("CORS_ORIGINS", "http://localhost:9001")

# ─── Produção (atrás do Apache com HTTPS) ────────────────────────────────────
# O Apache informa o protocolo original no cabeçalho X-Forwarded-Proto.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
# O redirecionamento HTTP → HTTPS é feito pelo Apache (certbot).
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "0") == "1"
# HSTS: só ligue depois de confirmar que o HTTPS funciona (ex.: 31536000 = 1 ano).
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
