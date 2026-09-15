"""As 7 casas da MCM abrangidas pelo contrato de gestao ambiental."""
from __future__ import annotations

from django.db import models

from apps.core.models import SoftDeleteModel, TimestampedModel, UUIDModel


class UF(models.TextChoices):
    TO = "TO", "Tocantins"
    MA = "MA", "Maranhao"
    PI = "PI", "Piaui"


class PotencialPoluidor(models.TextChoices):
    BAIXO = "BAIXO", "Baixo"
    MEDIO = "MEDIO", "Medio"
    ALTO = "ALTO", "Alto"


class SituacaoImovel(models.TextChoices):
    PROPRIO = "PROPRIO", "Proprio"
    LOCADO = "LOCADO", "Locado"
    AREA_TERCEIRO = "AREA_TERCEIRO", "Area licenciada de terceiro"


class UnidadeQuerySet(models.QuerySet):
    def ativos(self) -> UnidadeQuerySet:
        return self.filter(excluido_em__isnull=True)

    def com_oficina(self) -> UnidadeQuerySet:
        return self.filter(tem_oficina=True)

    def com_poco(self) -> UnidadeQuerySet:
        return self.filter(tem_poco=True)

    def em_posto(self) -> UnidadeQuerySet:
        return self.filter(opera_em_posto=True)

    def nunca_visitadas(self) -> UnidadeQuerySet:
        return self.filter(ultima_visita_tecnica__isnull=True)


class Unidade(UUIDModel, SoftDeleteModel, TimestampedModel):
    """Uma "casa" da MCM.

    As flags operacionais (`tem_oficina`, `tem_poco`, `opera_em_posto`,
    `imovel`) determinam quais requisitos legais sao aplicaveis. Alterar uma
    flag recalcula automaticamente o checklist da casa - nao ha lista fixa
    de documentos por unidade.
    """

    codigo = models.CharField("codigo", max_length=8, unique=True, db_index=True)
    nome = models.CharField("nome da casa", max_length=120)
    uf = models.CharField("UF", max_length=2, choices=UF.choices)
    municipio = models.CharField("municipio", max_length=80)
    cnpj = models.CharField("CNPJ", max_length=18, unique=True)
    endereco = models.TextField("endereco", blank=True)

    atividade = models.CharField("atividade", max_length=160, blank=True)
    porte = models.CharField("porte", max_length=20, blank=True)
    potencial_poluidor = models.CharField(
        "potencial poluidor",
        max_length=10,
        choices=PotencialPoluidor.choices,
        default=PotencialPoluidor.MEDIO,
    )
    imovel = models.CharField(
        "situacao do imovel",
        max_length=20,
        choices=SituacaoImovel.choices,
        default=SituacaoImovel.PROPRIO,
    )

    orgao_estadual = models.CharField("orgao ambiental estadual", max_length=80, blank=True)
    orgao_municipal = models.CharField("orgao ambiental municipal", max_length=80, blank=True)

    # ---------------------------------------------------- flags de aplicabilidade
    tem_oficina = models.BooleanField(
        "possui area de oficina/mecanica",
        default=True,
        help_text="Define a exigencia de SAO, laudo de efluente, ruido e monitoramento de solo.",
    )
    tem_poco = models.BooleanField(
        "possui captacao de agua subterranea",
        default=False,
        help_text="Define a exigencia de outorga, hidrometro e analise Marco Zero.",
    )
    opera_em_posto = models.BooleanField(
        "opera em area de posto de combustivel",
        default=False,
        help_text="Define a exigencia de teste de estanqueidade (Res. CONAMA 273/2000).",
    )

    responsavel_nome = models.CharField("coordenadora/responsavel", max_length=120, blank=True)
    responsavel_email = models.EmailField("e-mail do responsavel", blank=True)
    responsavel_cargo = models.CharField("cargo", max_length=120, blank=True)

    ultima_visita_tecnica = models.DateField("ultima visita tecnica", null=True, blank=True)
    diagnostico = models.TextField(
        "diagnostico da ultima visita",
        blank=True,
        help_text="Sintese do relatorio de auditoria da consultoria.",
    )

    objects = UnidadeQuerySet.as_manager()

    class Meta:
        verbose_name = "casa"
        verbose_name_plural = "casas"
        ordering = ("nome",)
        indexes = [models.Index(fields=["uf", "nome"])]

    def __str__(self) -> str:
        return self.nome

    @property
    def imovel_de_terceiro(self) -> bool:
        return self.imovel in {SituacaoImovel.LOCADO, SituacaoImovel.AREA_TERCEIRO}

    @property
    def destinatario_notificacao(self) -> str:
        """E-mail que recebe a cobranca desta casa."""
        usuario = self.usuarios.filter(is_active=True, recebe_notificacoes=True).first()
        return usuario.email if usuario else self.responsavel_email

    @property
    def sem_responsavel(self) -> bool:
        return not self.responsavel_email and not self.usuarios.filter(is_active=True).exists()
