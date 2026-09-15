"""Modelos base reutilizados por todo o sistema."""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class TimestampedModel(models.Model):
    """Carimbo de criacao e alteracao. Toda entidade do SIGA herda daqui."""

    criado_em = models.DateTimeField("criado em", auto_now_add=True, db_index=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Identificador publico estavel, seguro para expor em URLs e na API."""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def ativos(self) -> SoftDeleteQuerySet:
        return self.filter(excluido_em__isnull=True)

    def excluir(self):
        from django.utils import timezone

        return self.update(excluido_em=timezone.now())


class SoftDeleteModel(models.Model):
    """Exclusao logica: registro ambiental nunca some do historico."""

    excluido_em = models.DateTimeField("excluido em", null=True, blank=True, editable=False)

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):  # noqa: ARG002
        from django.utils import timezone

        self.excluido_em = timezone.now()
        self.save(update_fields=["excluido_em"])

    @property
    def ativo(self) -> bool:
        return self.excluido_em is None


class LogAuditoria(TimestampedModel):
    """Trilha imutavel: quem fez o que e quando.

    Alimentada por sinais e pela camada de servicos. Comprova diligencia da MCM
    perante o orgao ambiental (ABNT NBR ISO 14001:2015, item 7.5.3).
    """

    class Acao(models.TextChoices):
        CRIACAO = "CRIACAO", "Criou"
        ALTERACAO = "ALTERACAO", "Alterou"
        EXCLUSAO = "EXCLUSAO", "Excluiu"
        ENVIO = "ENVIO", "Enviou documento"
        VALIDACAO = "VALIDACAO", "Validou documento"
        REJEICAO = "REJEICAO", "Rejeitou documento"
        NOTIFICACAO = "NOTIFICACAO", "Disparou notificacao"
        EXPORTACAO = "EXPORTACAO", "Exportou relatorio"
        LOGIN = "LOGIN", "Autenticou"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
        verbose_name="usuario",
    )
    usuario_nome = models.CharField("nome do usuario", max_length=160, blank=True)
    acao = models.CharField("acao", max_length=20, choices=Acao.choices, db_index=True)
    objeto = models.CharField("objeto", max_length=255)
    detalhe = models.TextField("detalhe", blank=True)
    entidade = models.CharField("entidade", max_length=60, blank=True, db_index=True)
    entidade_id = models.CharField("id da entidade", max_length=60, blank=True)

    class Meta:
        verbose_name = "registro de auditoria"
        verbose_name_plural = "trilha de auditoria"
        ordering = ("-criado_em",)
        indexes = [models.Index(fields=["entidade", "entidade_id"])]

    def __str__(self) -> str:
        return f"{self.criado_em:%d/%m/%Y %H:%M} - {self.usuario_nome} - {self.get_acao_display()}"
