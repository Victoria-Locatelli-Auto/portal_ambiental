"""Ambiente de desenvolvimento."""
from .base import *  # noqa: F403
from .base import INSTALLED_APPS  # noqa: F401

DEBUG = True
ALLOWED_HOSTS = ["*"]
CELERY_TASK_ALWAYS_EAGER = True
