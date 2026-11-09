"""Movimentacao de residuos com rastreabilidade MTR/CDF."""
from __future__ import annotations

from django.db import models

from apps.core.models import TimestampedModel, UUIDModel


class ClasseResiduo(models.TextChoices):
    """Classificacao da ABNT NBR 10.004:2004."""

    CLASSE_I = "I", "Classe I - Perigoso"
    CLASSE_IIA = "IIA", "Classe II-A - Nao inerte"
    CLASSE_IIB = "IIB", "Classe II-B - Inerte"


class MovimentacaoQuerySet(models.QuerySet):
    def perigosos(self) -> MovimentacaoQuerySet:
        return self.filter(classe=ClasseResiduo.CLASSE_I)

    def sem_mtr(self) -> MovimentacaoQuerySet:
        return self.filter(numero_mtr="")

    def sem_cdf(self) -> MovimentacaoQuerySet:
        return self.filter(numero_cdf="")

    def sem_pesagem(self) -> MovimentacaoQuerySet:
        return self.filter(models.Q(quantidade__isnull=True) | models.Q(quantidade=0))


class MovimentacaoResiduo(UUIDModel, TimestampedModel):
    """Uma corrente de residuo gerada e destinada por uma casa.

    Sem MTR emitido no SINIR o destinador nao emite CDF valido, e sem CDF a MCM
    permanece corresponsavel pelo residuo (Lei 12.305/2010, art. 27, par. 1).
    O recibo de coleta da transportadora nao substitui o CDF.
    """

    class Unidade(models.TextChoices):
        KG = "kg", "quilogramas"
        L = "L", "litros"
        UN = "un", "unidades"
        T = "t", "toneladas"

    unidade = models.ForeignKey(
        "organizacao.Unidade",
        on_delete=models.PROTECT,
        related_name="residuos",
        verbose_name="casa",
    )
    residuo = models.CharField("residuo", max_length=160)
    classe = models.CharField("classe", max_length=3, choices=ClasseResiduo.choices)
    codigo_ibama = models.CharField("codigo do residuo", max_length=20, blank=True)
    quantidade = models.DecimalField(
        "quantidade",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Em branco quando a casa nao realiza pesagem.",
    )
    unidade_medida = models.CharField(
        "unidade de medida", max_length=4, choices=Unidade.choices, default=Unidade.KG
    )
    destinacao = models.CharField("destinacao final", max_length=120)
    destinador = models.CharField("empresa destinadora", max_length=160, blank=True)
    numero_mtr = models.CharField("numero do MTR (SINIR)", max_length=40, blank=True, db_index=True)
    numero_cdf = models.CharField("numero do CDF (SINIR)", max_length=40, blank=True)
    data_movimentacao = models.DateField("data")
    observacao = models.TextField("observacao da auditoria", blank=True)

    objects = MovimentacaoQuerySet.as_manager()

    class Meta:
        verbose_name = "movimentacao de residuo"
        verbose_name_plural = "movimentacoes de residuos"
        ordering = ("-data_movimentacao",)
        indexes = [models.Index(fields=["unidade", "classe"])]

    def __str__(self) -> str:
        return f"{self.residuo} - {self.unidade.nome}"

    @property
    def rastreavel(self) -> bool:
        """True somente quando ha MTR e CDF - a unica prova de destinacao."""
        return bool(self.numero_mtr and self.numero_cdf)

    @property
    def pesado(self) -> bool:
        return bool(self.quantidade)
