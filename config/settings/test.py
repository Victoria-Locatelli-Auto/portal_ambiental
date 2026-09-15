"""Ambiente de teste: banco em memoria, e-mail capturado e sem estaticos."""
from .base import *  # noqa: F403
from .base import MIDDLEWARE

DEBUG = False
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Sem whitenoise nem manifesto de estaticos: os testes nao dependem de collectstatic.
MIDDLEWARE = [m for m in MIDDLEWARE if "whitenoise" not in m.lower()]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
