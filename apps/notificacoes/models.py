"""Registro dos e-mails disparados pela regua de vencimentos."""
from __future__ import annotations

from django.db import models

from apps.core.models import TimestampedModel, UUIDModel


class TipoNotificacao(models.TextChoices):
    ALERTA = "ALERTA", "Alerta de vencimento"
    VENCIDO = "VENCIDO", "Documento vencido"
    COBRANCA = "COBRANCA", "Cobranca de checklist"
    RECEBIMENTO = "RECEBIMENTO", "Documento recebido"
    VALIDACAO = "VALIDACAO", "Documento validado"
    RESUMO = "RESUMO", "Resumo gerencial"


class ModeloEmail(TimestampedModel):
    """Assunto e corpo editáveis dos e-mails automáticos do SIGA."""

    tipo = models.CharField(
        "tipo de notificação", max_length=15, choices=TipoNotificacao.choices, unique=True
    )
    assunto = models.CharField(
        "assunto", max_length=255,
        help_text="Aceita variáveis no formato {{ unidade.nome }}.",
    )
    corpo = models.TextField(
        "texto do e-mail",
        help_text="Aceita variáveis e estruturas da linguagem de templates do Django.",
    )
    ativo = models.BooleanField("ativo", default=True)

    class Meta:
        verbose_name = "modelo de e-mail"
        verbose_name_plural = "modelos de e-mail"
        ordering = ("tipo",)

    def __str__(self) -> str:
        return self.get_tipo_display()


class Notificacao(UUIDModel, TimestampedModel):
    """Uma mensagem efetivamente enviada. Serve de prova de diligencia."""

    class Situacao(models.TextChoices):
        ENFILEIRADA = "ENFILEIRADA", "Enfileirada"
        ENVIADA = "ENVIADA", "Enviada"
        FALHA = "FALHA", "Falha no envio"

    tipo = models.CharField("tipo", max_length=15, choices=TipoNotificacao.choices, db_index=True)
    unidade = models.ForeignKey(
        "organizacao.Unidade",
        on_delete=models.CASCADE,
        related_name="notificacoes",
        null=True,
        blank=True,
    )
    documento = models.ForeignKey(
        "compliance.Documento",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notificacoes",
    )
    gatilho_dias = models.IntegerField(
        "gatilho (dias)", null=True, blank=True, help_text="Negativo quando ja vencido."
    )
    destinatario = models.EmailField("destinatario")
    copias = models.TextField("copias", blank=True)
    assunto = models.CharField("assunto", max_length=255)
    corpo = models.TextField("corpo")
    situacao = models.CharField(
        "situacao", max_length=12, choices=Situacao.choices, default=Situacao.ENFILEIRADA
    )
    enviada_em = models.DateTimeField("enviada em", null=True, blank=True)
    erro = models.TextField("erro", blank=True)
    chave_idempotencia = models.CharField(
        "chave de idempotencia",
        max_length=180,
        db_index=True,
        help_text="Impede o reenvio do mesmo gatilho no mesmo dia.",
    )

    class Meta:
        verbose_name = "notificacao"
        verbose_name_plural = "notificacoes"
        ordering = ("-criado_em",)
        constraints = [
            models.UniqueConstraint(
                fields=["chave_idempotencia"], name="notificacao_idempotente"
            )
        ]

    def __str__(self) -> str:
        return f"[{self.get_tipo_display()}] {self.assunto[:70]}"


class NotificacaoSistema(UUIDModel, TimestampedModel):
    """Aviso individual exibido dentro do SIGA."""

    usuario = models.ForeignKey(
        "accounts.Usuario",
        on_delete=models.CASCADE,
        related_name="notificacoes_sistema",
        verbose_name="usuário",
    )
    origem_email = models.ForeignKey(
        Notificacao,
        on_delete=models.CASCADE,
        related_name="avisos_sistema",
        verbose_name="notificação de origem",
    )
    tipo = models.CharField("tipo", max_length=15, choices=TipoNotificacao.choices, db_index=True)
    unidade = models.ForeignKey(
        "organizacao.Unidade",
        on_delete=models.CASCADE,
        related_name="notificacoes_sistema",
        null=True,
        blank=True,
    )
    documento = models.ForeignKey(
        "compliance.Documento",
        on_delete=models.SET_NULL,
        related_name="notificacoes_sistema",
        null=True,
        blank=True,
    )
    titulo = models.CharField("título", max_length=255)
    mensagem = models.TextField("mensagem")
    link = models.CharField("link interno", max_length=300, blank=True)
    lida_em = models.DateTimeField("lida em", null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = "notificação no sistema"
        verbose_name_plural = "notificações no sistema"
        ordering = ("-criado_em",)
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "origem_email"],
                name="notificacao_sistema_unica_por_usuario",
            )
        ]
        indexes = [models.Index(fields=["usuario", "lida_em", "criado_em"])]

    def __str__(self) -> str:
        return f"{self.usuario}: {self.titulo[:70]}"

    @property
    def lida(self) -> bool:
        return self.lida_em is not None
