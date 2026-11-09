"""Configuracao do Celery e agendamento da regua de notificacoes."""
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("siga")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "regua-diaria-de-vencimentos": {
        "task": "apps.notificacoes.tasks.processar_regua_diaria",
        "schedule": crontab(hour=7, minute=30),
    },
    "cobranca-semanal-de-checklist": {
        "task": "apps.notificacoes.tasks.enviar_cobrancas_semanais",
        "schedule": crontab(hour=7, minute=30, day_of_week="mon"),
    },
    "resumo-gerencial-mensal": {
        "task": "apps.notificacoes.tasks.enviar_resumo_gerencial",
        "schedule": crontab(hour=8, minute=0, day_of_month="1"),
    },
}
