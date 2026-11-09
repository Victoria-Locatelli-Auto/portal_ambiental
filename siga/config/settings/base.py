"""Configuracao comum a todos os ambientes."""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parents[2]

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
environ.Env.read_env(BASE_DIR / ".env")
environ.Env.read_env(BASE_DIR / ".env.local", overwrite=True)

SECRET_KEY = env("SECRET_KEY", default="dev-inseguro-troque-em-producao")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# --------------------------------------------------------------------------- apps
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.humanize",
    "django.contrib.staticfiles",
]
THIRD_PARTY_APPS = [
    "rest_framework",
    "django_filters",
]
LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.organizacao",
    "apps.compliance",
    "apps.auditoria",
    "apps.residuos",
    "apps.notificacoes",
    "apps.dashboard",
    "apps.fornecedores",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.UsuarioAtualMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.siga",
                "apps.notificacoes.context_processors.notificacoes_nao_lidas",
            ],
        },
    },
]

# --------------------------------------------------------------------------- dados
DATABASES = {"default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR/'db.sqlite3'}")}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.Usuario"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard:painel"
LOGOUT_REDIRECT_URL = "login"

# --------------------------------------------------------------------------- i18n
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------- arquivos
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
# O manifesto comprimido do whitenoise exige `collectstatic` e so e usado em producao
# (config/settings/prod.py). Em dev e em teste isso seria um pe no caminho.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20 MB

# --------------------------------------------------------------------------- e-mail
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="SIGA MCM <siga@mcm.com.br>")
MICROSOFT_CLIENT_ID = env("MICROSOFT_CLIENT_ID", default="")
MICROSOFT_TENANT_ID = env("MICROSOFT_TENANT_ID", default="")
MICROSOFT_CLIENT_SECRET = env("MICROSOFT_CLIENT_SECRET", default="")
MICROSOFT_SENDER_EMAIL = env("MICROSOFT_SENDER_EMAIL", default="")

# --------------------------------------------------------------------------- celery
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=CELERY_BROKER_URL)
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = False

# --------------------------------------------------------------------------- DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

# --------------------------------------------------------------------------- SIGA
SIGA = {
    "NOME": "SIGA",
    "DESCRICAO": "Sistema Integrado de Gestao Ambiental",
    "ORGANIZACAO": "MCM Comercio de Caminhoes e Onibus Ltda.",
    "CONSULTORIA": "STX Engenharia e Meio Ambiente Ltda.",
    "CONSULTORIA_CNPJ": "39.966.950/0001-00",
    "RESPONSAVEL_TECNICO": "Tales Goncalves Pereira - Eng. Ambiental - CREA-TO 307764/D",
    # Alertas são enviados diariamente dentro da antecedência de cada tipo documental.
    "DIAS_CRITICO": 30,
    "DIAS_ALERTA": 90,
    # Prazo legal do art. 18, par. 4, da Res. CONAMA 237/1997
    "DIAS_PROTOCOLO_RENOVACAO_LO": 120,
    "ESCALONAR_DIRETORIA_APOS_DIAS": 15,
    "EMAIL_CONSULTORIA": env("SIGA_EMAIL_CONSULTORIA", default="stxambiental@gmail.com"),
    "EMAIL_GESTAO": env("SIGA_EMAIL_GESTAO", default="ambiental@mcm.com.br"),
    "EMAIL_DIRETORIA": env("SIGA_EMAIL_DIRETORIA", default="diretoria@mcm.com.br"),
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simples": {"format": "{levelname} {asctime} {name} {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simples"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {"apps": {"handlers": ["console"], "level": "DEBUG", "propagate": False}},
}
