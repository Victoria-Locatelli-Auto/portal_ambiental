from __future__ import annotations

from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.models import TimestampedModel, UUIDModel


def caminho_anexo_fornecedor(instance: Fornecedor, filename: str) -> str:
    return f"fornecedores/{instance.uuid}/cadastro/{filename}"


class Fornecedor(UUIDModel, TimestampedModel):
    razao_social = models.CharField("razão social", max_length=180)
    nome_fantasia = models.CharField("nome fantasia", max_length=180, blank=True)
    cnpj_cpf = models.CharField("CNPJ/CPF", max_length=18, unique=True)
    servico_fornecido = models.CharField("produto ou serviço fornecido", max_length=220)
    responsavel = models.CharField("pessoa de contato", max_length=160, blank=True)
    email = models.EmailField("e-mail", blank=True)
    telefone = models.CharField("telefone", max_length=32, blank=True)
    endereco = models.CharField("endereço", max_length=255, blank=True)
    observacoes = models.TextField("observações", blank=True)
    anexo_contrato = models.FileField(
        "anexo do contrato",
        upload_to=caminho_anexo_fornecedor,
        blank=True,
        validators=[FileExtensionValidator(["pdf", "doc", "docx", "odt"])],
        help_text="Anexe o contrato em PDF, DOC, DOCX ou ODT.",
    )
    cidades_atendidas = models.ManyToManyField(
        "organizacao.Unidade",
        blank=True,
        related_name="fornecedores",
        verbose_name="cidades atendidas",
    )
    ativo = models.BooleanField("ativo", default=True, db_index=True)

    class Meta:
        verbose_name = "fornecedor"
        verbose_name_plural = "fornecedores"
        ordering = ("razao_social",)

    def __str__(self) -> str:
        return self.nome_fantasia or self.razao_social


class SituacaoContrato(models.TextChoices):
    VIGENTE = "VIGENTE", "Vigente"
    ENCERRADO = "ENCERRADO", "Encerrado"
    SUSPENSO = "SUSPENSO", "Suspenso"
    CANCELADO = "CANCELADO", "Cancelado"


def caminho_contrato(instance: Contrato, filename: str) -> str:
    return f"fornecedores/{instance.fornecedor.uuid}/contratos/{filename}"


class Contrato(UUIDModel, TimestampedModel):
    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.PROTECT,
        related_name="contratos",
        verbose_name="fornecedor",
    )
    numero = models.CharField("número do contrato", max_length=80)
    objeto = models.TextField("objeto do contrato")
    data_inicio = models.DateField("início da vigência")
    data_fim = models.DateField("fim da vigência")
    valor = models.DecimalField(
        "valor do contrato",
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    situacao = models.CharField(
        "situação", max_length=12, choices=SituacaoContrato.choices,
        default=SituacaoContrato.VIGENTE, db_index=True,
    )
    arquivo = models.FileField(
        "arquivo do contrato",
        upload_to=caminho_contrato,
        blank=True,
        validators=[FileExtensionValidator(["pdf", "doc", "docx", "odt"])],
        help_text="Formatos aceitos: PDF, DOC, DOCX ou ODT.",
    )
    observacoes = models.TextField("observações", blank=True)

    class Meta:
        verbose_name = "contrato"
        verbose_name_plural = "contratos"
        ordering = ("-data_fim", "numero")
        constraints = [
            models.UniqueConstraint(
                fields=("fornecedor", "numero"), name="contrato_numero_unico_fornecedor"
            )
        ]

    def __str__(self) -> str:
        return f"{self.numero} — {self.fornecedor}"

    @property
    def vencido(self) -> bool:
        return self.data_fim < timezone.localdate()

