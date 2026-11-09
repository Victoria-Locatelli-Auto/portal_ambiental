"""Sinais que alimentam a trilha de auditoria sem poluir a camada de servicos."""
from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.compliance.models import Condicionante
from apps.core.models import LogAuditoria
from apps.core.services import registrar


@receiver(post_save, sender=Condicionante)
def log_condicionante(sender, instance: Condicionante, created: bool, **kwargs):  # noqa: ARG001
    registrar(
        LogAuditoria.Acao.CRIACAO if created else LogAuditoria.Acao.ALTERACAO,
        f"Condicionante - {instance.unidade.nome}",
        detalhe=f"{instance.get_situacao_display()} | {instance.descricao[:120]}",
        entidade="Condicionante",
        entidade_id=instance.pk,
    )
