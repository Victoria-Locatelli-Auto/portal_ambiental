"""Auditoria interna: relatorios de visita, checklist de campo e nao conformidades."""
from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import TimestampedModel, UUIDModel
from apps.core.utils import dias_ate


class RelatorioAuditoria(UUIDModel, TimestampedModel):
    """Relatorio de auditoria e monitoramento interno emitido pela consultoria.

    O contrato preve 2 visitas tecnicas por ano por casa.
    """

    unidade = models.ForeignKey(
        "organizacao.Unidade",
        on_delete=models.CASCADE,
        related_name="relatorios",
        verbose_name="casa",
    )
    numero = models.CharField("numero", max_length=20)
    data_visita = models.DateField("data da visita in loco")
    data_emissao = models.DateField("data de emissao")
    responsavel_tecnico = models.CharField("responsavel tecnico", max_length=160)
    acompanhante = models.CharField("acompanhado por", max_length=160, blank=True)
    arquivo = models.FileField("arquivo", upload_to="relatorios/%Y/", blank=True)
    recebido = models.BooleanField(
        "arquivo recebido",
        default=True,
        help_text="Falso quando o acervo tem apenas a referencia, sem o PDF.",
    )
    sintese = models.TextField("sintese do diagnostico", blank=True)

    class Meta:
        verbose_name = "relatorio de auditoria"
        verbose_name_plural = "relatorios de auditoria"
        ordering = ("-data_emissao",)
        constraints = [
            models.UniqueConstraint(fields=["unidade", "numero"], name="relatorio_unico_por_casa")
        ]

    def __str__(self) -> str:
        return f"Relatorio {self.numero} - {self.unidade.nome}"


class PontoVerificacao(TimestampedModel):
    """Pergunta do checklist aplicado pela consultoria na visita in loco."""

    ordem = models.PositiveSmallIntegerField("ordem", default=0)
    pergunta = models.CharField("ponto verificado", max_length=255, unique=True)
    referencia_legal = models.CharField("referencia legal", max_length=200, blank=True)

    class Meta:
        verbose_name = "ponto de verificacao"
        verbose_name_plural = "checklist de campo"
        ordering = ("ordem",)

    def __str__(self) -> str:
        return self.pergunta


class RespostaCampo(TimestampedModel):
    """Resposta registrada em ata para uma casa em uma visita."""

    class Resultado(models.TextChoices):
        CONFORME = "C", "Conforme"
        PARCIAL = "P", "Parcial / a comprovar"
        NAO_CONFORME = "N", "Nao conforme"
        NAO_APLICAVEL = "NA", "Nao aplicavel"

    relatorio = models.ForeignKey(
        RelatorioAuditoria, on_delete=models.CASCADE, related_name="respostas"
    )
    ponto = models.ForeignKey(PontoVerificacao, on_delete=models.PROTECT, related_name="respostas")
    resultado = models.CharField("resultado", max_length=2, choices=Resultado.choices)
    observacao = models.TextField("resposta registrada")

    class Meta:
        verbose_name = "resposta de campo"
        verbose_name_plural = "respostas de campo"
        ordering = ("ponto__ordem",)
        constraints = [
            models.UniqueConstraint(
                fields=["relatorio", "ponto"], name="resposta_unica_por_relatorio_e_ponto"
            )
        ]

    def __str__(self) -> str:
        return f"{self.relatorio.unidade.nome} - {self.ponto.pergunta[:50]}"


class NaoConformidadeQuerySet(models.QuerySet):
    def abertas(self) -> NaoConformidadeQuerySet:
        return self.exclude(situacao=NaoConformidade.Situacao.ENCERRADA)

    def criticas(self) -> NaoConformidadeQuerySet:
        return self.filter(gravidade=NaoConformidade.Gravidade.CRITICA)

    def em_atraso(self) -> NaoConformidadeQuerySet:
        from apps.core.utils import hoje

        return self.abertas().filter(prazo__lt=hoje())


class NaoConformidade(UUIDModel, TimestampedModel):
    """Desvio legal ou operacional com plano de acao estruturado em 5W2H.

    Atende ao requisito 10.2 da ABNT NBR ISO 14001:2015.
    """

    class Gravidade(models.TextChoices):
        CRITICA = "CRITICA", "Critica"
        ALTA = "ALTA", "Alta"
        MEDIA = "MEDIA", "Media"
        BAIXA = "BAIXA", "Baixa"

    class Situacao(models.TextChoices):
        ABERTA = "ABERTA", "Aberta"
        EM_TRATAMENTO = "EM_TRATAMENTO", "Em tratamento"
        ENCERRADA = "ENCERRADA", "Encerrada"

    class Origem(models.TextChoices):
        AUDITORIA = "AUDITORIA", "Auditoria interna"
        VISITA = "VISITA", "Visita tecnica"
        DOCUMENTAL = "DOCUMENTAL", "Analise documental"
        FISCALIZACAO = "FISCALIZACAO", "Fiscalizacao do orgao"
        SISTEMA = "SISTEMA", "Deteccao automatica do SIGA"

    codigo = models.CharField("codigo", max_length=20, unique=True, db_index=True)
    unidade = models.ForeignKey(
        "organizacao.Unidade", on_delete=models.PROTECT, related_name="nao_conformidades"
    )
    origem = models.CharField("origem", max_length=15, choices=Origem.choices)
    data_abertura = models.DateField("data de abertura")
    descricao = models.TextField("descricao do desvio")
    requisito_violado = models.CharField("requisito legal violado", max_length=255)
    gravidade = models.CharField("gravidade", max_length=10, choices=Gravidade.choices)
    situacao = models.CharField(
        "situacao", max_length=15, choices=Situacao.choices, default=Situacao.ABERTA
    )
    relatorio = models.ForeignKey(
        RelatorioAuditoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nao_conformidades",
    )

    # ------------------------------------------------------------------ 5W2H
    o_que = models.TextField("What - o que sera feito")
    por_que = models.TextField("Why - por que")
    onde = models.CharField("Where - onde", max_length=160)
    quem = models.CharField("Who - quem", max_length=160)
    prazo = models.DateField("When - prazo")
    como = models.TextField("How - como")
    quanto = models.CharField("How much - quanto", max_length=120, blank=True)
    custo_estimado = models.DecimalField(
        "custo estimado (R$)", max_digits=12, decimal_places=2, null=True, blank=True
    )

    encerrada_em = models.DateField("encerrada em", null=True, blank=True)
    evidencia_encerramento = models.TextField("evidencia do encerramento", blank=True)
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    objects = NaoConformidadeQuerySet.as_manager()

    class Meta:
        verbose_name = "nao conformidade"
        verbose_name_plural = "nao conformidades"
        ordering = ("gravidade", "prazo")
        indexes = [models.Index(fields=["situacao", "gravidade"])]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.unidade.nome}"

    @property
    def dias_para_prazo(self) -> int | None:
        return dias_ate(self.prazo)

    @property
    def prazo_vencido(self) -> bool:
        d = self.dias_para_prazo
        return d is not None and d < 0 and self.situacao != self.Situacao.ENCERRADA
