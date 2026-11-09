"""Ambiente de producao."""
from .base import *  # noqa: F403

DEBUG = False
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405
FORCE_SCRIPT_NAME = env("FORCE_SCRIPT_NAME", default=None)  # noqa: F405
STATIC_URL = env("STATIC_URL", default="/static/")  # noqa: F405

# O SIGA pode ser publicado abaixo de outro portal no mesmo dominio. Cookies
# com nomes e caminho proprios evitam conflito com a sessao/CSRF do portal.
_cookie_path = f"{FORCE_SCRIPT_NAME.rstrip('/')}/" if FORCE_SCRIPT_NAME else "/"
CSRF_COOKIE_NAME = env("CSRF_COOKIE_NAME", default="siga_csrftoken")  # noqa: F405
SESSION_COOKIE_NAME = env("SESSION_COOKIE_NAME", default="siga_sessionid")  # noqa: F405
CSRF_COOKIE_PATH = env("CSRF_COOKIE_PATH", default=_cookie_path)  # noqa: F405
SESSION_COOKIE_PATH = env("SESSION_COOKIE_PATH", default=_cookie_path)  # noqa: F405

# Permite manter arquivos persistentes fora da pasta do codigo na VPS.
STATIC_ROOT = Path(env("STATIC_ROOT", default="/var/www/siga/staticfiles"))  # noqa: F405
MEDIA_ROOT = Path(env("MEDIA_ROOT", default="/var/lib/siga/media"))  # noqa: F405

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# HSTS comeca conservador e pode ser elevado apos validar HTTPS e subdominios.
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=3600)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(  # noqa: F405
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False
)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)  # noqa: F405
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"

# Estaticos versionados e comprimidos. Exige `python manage.py collectstatic`.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
