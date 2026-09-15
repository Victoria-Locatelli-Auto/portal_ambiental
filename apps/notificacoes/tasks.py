"""Tarefas agendadas do Celery. O agendamento vive em config/celery.py."""
from __future__ import annotations

import logging

from celery import shared_task

from apps.notificacoes import services

logger = logging.getLogger(__name__)


@shared_task(name="apps.notificacoes.tasks.processar_regua_diaria")
def processar_regua_diaria() -> int:
    """Alertas de vencimento e avisos de documento vencido. Roda todo dia as 07:30."""
    enviadas = services.processar_alertas()
    logger.info("Regua diaria: %s notificacao(oes) enviada(s)", len(enviadas))
    return len(enviadas)


@shared_task(name="apps.notificacoes.tasks.enviar_cobrancas_semanais")
def enviar_cobrancas_semanais() -> int:
    """Uma cobranca consolidada por casa. Roda toda segunda as 07:30."""
    enviadas = services.processar_cobrancas()
    logger.info("Cobranca semanal: %s casa(s) notificada(s)", len(enviadas))
    return len(enviadas)


@shared_task(name="apps.notificacoes.tasks.enviar_resumo_gerencial")
def enviar_resumo_gerencial() -> int:
    """Consolidado mensal para a gestao. Roda no dia 1."""
    from django.conf import settings
    from django.core.mail import send_mail
    from apps.compliance.selectors import resumo_geral
    from apps.organizacao.models import Unidade

    resumos = resumo_geral(Unidade.objects.ativos())
    assunto, corpo = services.renderizar_email(
        "RESUMO",
        {"resumos": resumos},
        "[SIGA-MCM] Resumo gerencial mensal de conformidade ambiental",
        "notificacoes/email_resumo.txt",
    )
    send_mail(
        subject=assunto,
        message=corpo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.SIGA["EMAIL_GESTAO"]],
        fail_silently=False,
    )
    return len(resumos)
