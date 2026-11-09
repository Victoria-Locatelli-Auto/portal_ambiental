"""Catalogo de requisitos legais e acervo documental das casas."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.validators import RegexValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.compliance.enums import (
    Aplicabilidade,
    ResponsavelExecucao,
    SituacaoDocumento,
    StatusConformidade,
    TemaLegal,
    UNIDADE_PREFIXO,
    codigo_unidade,
    valor_unidade,
)
from apps.core.models import SoftDeleteModel, TimestampedModel, UUIDModel
from apps.core.utils import dias_ate, hoje, somar_meses


class TemaLegalCadastro(TimestampedModel):
    codigo = models.CharField(
        "código",
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z0-9_]+$",
                message="Use somente letras maiúsculas, números e sublinhado.",
            )
        ],
    )
    nome = models.CharField("nome", max_length=120, unique=True)
    ordem = models.PositiveSmallIntegerField("ordem de exibição", default=0)
    ativo = models.BooleanField("ativo", default=True, db_index=True)

    class Meta:
        verbose_name = "tema legal"
        verbose_name_plural = "temas legais"
        ordering = ("ordem", "nome")

    def __str__(self) -> str:
        return self.nome


class NormaLegal(TimestampedModel):
    """Norma que fundamenta um ou mais requisitos documentais."""

    class Esfera(models.TextChoices):
        FEDERAL = "FEDERAL", "Federal"
        ESTADUAL = "ESTADUAL", "Estadual"
        MUNICIPAL = "MUNICIPAL", "Municipal"
        TECNICA = "TECNICA", "Norma tecnica"

    identificacao = models.CharField("norma", max_length=160, unique=True)
    objeto = models.TextField("objeto")
    esfera = models.CharField("esfera", max_length=12, choices=Esfera.choices)
    url = models.URLField("link oficial", blank=True)

    class Meta:
        verbose_name = "norma legal"
        verbose_name_plural = "base legal"
        ordering = ("esfera", "identificacao")

    def __str__(self) -> str:
        return self.identificacao


class TipoDocumentoQuerySet(models.QuerySet):
    def ativos(self) -> TipoDocumentoQuerySet:
        return self.filter(ativo=True)

    def aplicaveis_a(self, unidade) -> TipoDocumentoQuerySet:
        """Requisitos exigiveis desta casa, conforme as flags operacionais."""
        regras = [Aplicabilidade.TODAS]
        if unidade.tem_oficina:
            regras.append(Aplicabilidade.OFICINA)
        if unidade.tem_poco:
            regras.append(Aplicabilidade.POCO)
        if unidade.opera_em_posto:
            regras.append(Aplicabilidade.POSTO)
        if unidade.imovel_de_terceiro:
            regras.append(Aplicabilidade.IMOVEL_TERCEIRO)
        regras.append(valor_unidade(unidade.codigo))
        consulta = models.Q()
        for regra in regras:
            consulta |= models.Q(aplicabilidade__contains=regra)
        return self.ativos().filter(consulta)

    def do_checklist_da_casa(self) -> TipoDocumentoQuerySet:
        """Itens executados pela casa - os que geram cobranca a coordenadora."""
        consulta = models.Q()
        for responsavel in ResponsavelExecucao.da_casa():
            consulta |= models.Q(responsavel_execucao__contains=responsavel)
        consulta |= models.Q(responsavel_execucao__contains=UNIDADE_PREFIXO)
        return self.filter(consulta)


class CorAgenda(models.TextChoices):
    VERDE = "VERDE", "Verde"
    MARROM = "MARROM", "Marrom"
    AZUL = "AZUL", "Azul"
    SEM_COR = "SEM_COR", "Sem cor"


class TipoDocumento(UUIDModel, TimestampedModel):
    """Um requisito legal documental.

    Cada tipo amarra: o documento exigido, a norma que o obriga, a validade,
    o gatilho de alerta, a quem se aplica e a instrucao em linguagem direta
    para a coordenadora da casa.
    """

    codigo = models.CharField("codigo", max_length=8, unique=True, db_index=True)
    nome = models.CharField("documento exigido", max_length=200)
    tema = models.CharField("tema legal", max_length=20, choices=TemaLegal.choices)
    cor_agenda = models.CharField(
        "cor da agenda", max_length=10, choices=CorAgenda.choices, default=CorAgenda.VERDE
    )

    periodicidade_meses = models.PositiveSmallIntegerField(
        "validade em meses",
        default=12,
        help_text="0 = documento por evento, sem prazo de validade fixo.",
    )
    quantidade_arquivos = models.PositiveSmallIntegerField(
        "quantidade de documentos",
        choices=((1, "1 documento"), (2, "2 documentos relacionados")),
        default=1,
    )
    nome_anexo_complementar = models.CharField(
        "nome do segundo documento",
        max_length=120,
        blank=True,
        help_text="Ex.: Certificado.",
    )
    dias_alerta = models.PositiveSmallIntegerField(
        "antecedencia do alerta (dias)",
        default=60,
        validators=[MinValueValidator(1)],
        help_text="A partir de quantos dias antes do vencimento o SIGA comeca a avisar.",
    )
    aplicabilidade = models.CharField("aplicabilidade", max_length=255, default=Aplicabilidade.TODAS)
    responsavel_execucao = models.CharField(
        "quem executa", max_length=255, default=ResponsavelExecucao.CASA,
    )

    base_legal = models.TextField("fundamento legal")
    normas = models.ManyToManyField(
        NormaLegal, blank=True, related_name="tipos_documento", verbose_name="normas vinculadas"
    )
    instrucao = models.TextField(
        "o que a coordenadora precisa fazer",
        help_text="Texto direto exibido no checklist da casa.",
    )
    nota_tecnica = models.TextField("observacao tecnica", blank=True)
    ordem = models.PositiveSmallIntegerField("ordem de exibicao", default=100)
    ativo = models.BooleanField("ativo", default=True)

    objects = TipoDocumentoQuerySet.as_manager()

    class Meta:
        verbose_name = "tipo documental"
        verbose_name_plural = "catalogo de requisitos legais"
        ordering = ("ordem", "codigo")
        indexes = [models.Index(fields=["tema", "ordem"])]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome}"

    @property
    def tema_rotulo(self) -> str:
        cadastro = TemaLegalCadastro.objects.filter(codigo=self.tema).only("nome").first()
        return cadastro.nome if cadastro else self.get_tema_display()

    @property
    def por_evento(self) -> bool:
        return self.periodicidade_meses == 0

    @property
    def e_do_checklist_da_casa(self) -> bool:
        return any(
            valor in ResponsavelExecucao.da_casa() or codigo_unidade(valor)
            for valor in self.responsaveis_execucao
        )

    @staticmethod
    def _valores_multiplos(valor: str) -> list[str]:
        return [item.strip() for item in (valor or "").split(",") if item.strip()]

    @property
    def aplicabilidades(self) -> list[str]:
        return self._valores_multiplos(self.aplicabilidade)

    @property
    def responsaveis_execucao(self) -> list[str]:
        return self._valores_multiplos(self.responsavel_execucao)

    def get_aplicabilidade_display(self) -> str:
        return self._display_com_casas(self.aplicabilidades, dict(Aplicabilidade.choices))

    def get_responsavel_execucao_display(self) -> str:
        return self._display_com_casas(
            self.responsaveis_execucao, dict(ResponsavelExecucao.choices)
        )

    @staticmethod
    def _display_com_casas(valores: list[str], rotulos: dict[str, str]) -> str:
        codigos = [codigo for valor in valores if (codigo := codigo_unidade(valor))]
        if codigos:
            from apps.organizacao.models import Unidade

            nomes = dict(
                Unidade.objects.filter(codigo__in=codigos).values_list("codigo", "nome")
            )
            rotulos.update({valor_unidade(codigo): nome for codigo, nome in nomes.items()})
        return ", ".join(rotulos.get(item, item) for item in valores)

    def calcular_vencimento(self, emissao: date) -> date | None:
        """Vencimento sugerido a partir da emissao e da periodicidade."""
        if self.por_evento:
            return None
        return somar_meses(emissao, self.periodicidade_meses)

    def aplica_a(self, unidade) -> bool:
        for regra in self.aplicabilidades:
            if regra == Aplicabilidade.TODAS:
                return True
            if codigo := codigo_unidade(regra):
                if codigo == unidade.codigo:
                    return True
            elif regra == Aplicabilidade.OFICINA and unidade.tem_oficina:
                return True
            elif regra == Aplicabilidade.POCO and unidade.tem_poco:
                return True
            elif regra == Aplicabilidade.POSTO and unidade.opera_em_posto:
                return True
            elif regra == Aplicabilidade.IMOVEL_TERCEIRO and unidade.imovel_de_terceiro:
                return True
        return False


class DocumentoQuerySet(models.QuerySet):
    def ativos(self) -> DocumentoQuerySet:
        return self.filter(excluido_em__isnull=True)

    def vigentes(self) -> DocumentoQuerySet:
        """Apenas a versao corrente de cada par (casa, tipo)."""
        return self.ativos().filter(versao_corrente=True)

    def da_unidade(self, unidade) -> DocumentoQuerySet:
        return self.filter(unidade=unidade)

    def aguardando_validacao(self) -> DocumentoQuerySet:
        return self.vigentes().filter(situacao=SituacaoDocumento.AGUARDANDO)

    def vencidos(self, referencia: date | None = None) -> DocumentoQuerySet:
        return self.vigentes().filter(
            data_vencimento__lt=referencia or hoje(), situacao=SituacaoDocumento.VALIDADO
        )

    def vencendo_ate(self, dias: int, referencia: date | None = None) -> DocumentoQuerySet:
        base = referencia or hoje()
        return self.vigentes().filter(
            data_vencimento__gte=base,
            data_vencimento__lte=somar_meses(base, 0).replace() + timezone.timedelta(days=dias),
        )


def caminho_do_arquivo(instancia: "Documento", nome_original: str) -> str:
    """media/documentos/<casa>/<tipo>/<ano>/<arquivo>"""
    return (
        f"documentos/{instancia.unidade.codigo}/{instancia.tipo.codigo}/"
        f"{instancia.data_emissao:%Y}/{nome_original}"
    )


def caminho_do_anexo_renovacao(instancia: "AnexoProcessoRenovacao", nome_original: str) -> str:
    """media/renovacoes/<casa>/<processo>/<arquivo>."""
    return (
        f"renovacoes/{instancia.processo.unidade.codigo}/"
        f"{instancia.processo.uuid}/{nome_original}"
    )


class Documento(UUIDModel, SoftDeleteModel, TimestampedModel):
    """Uma versao de um documento enviado por uma casa.

    O envio de um novo documento do mesmo tipo cria uma nova versao e arquiva
    a anterior. O historico nunca e apagado - exigencia de rastreabilidade.
    """

    unidade = models.ForeignKey(
        "organizacao.Unidade",
        on_delete=models.PROTECT,
        related_name="documentos",
        verbose_name="casa",
    )
    tipo = models.ForeignKey(
        TipoDocumento,
        on_delete=models.PROTECT,
        related_name="documentos",
        verbose_name="tipo documental",
    )
    fornecedor = models.ForeignKey(
        "fornecedores.Fornecedor",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="documentos",
        verbose_name="fornecedor",
    )
    identificacao = models.CharField(
        "identificacao", max_length=255, help_text="Numero, orgao emissor e revisao."
    )
    numero_protocolo = models.CharField("numero do protocolo", max_length=120, blank=True)
    arquivo = models.FileField("arquivo", upload_to=caminho_do_arquivo, blank=True)
    anexo_complementar = models.FileField(
        "segundo documento", upload_to=caminho_do_arquivo, blank=True
    )
    nome_anexo_complementar = models.CharField(
        "nome do segundo documento", max_length=120, blank=True
    )

    data_emissao = models.DateField("data de emissao")
    data_vencimento = models.DateField("data de vencimento", null=True, blank=True, db_index=True)

    situacao = models.CharField(
        "situacao",
        max_length=12,
        choices=SituacaoDocumento.choices,
        default=SituacaoDocumento.AGUARDANDO,
        db_index=True,
    )
    versao = models.PositiveSmallIntegerField("versao", default=1)
    versao_corrente = models.BooleanField("versao corrente", default=True, db_index=True)

    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_enviados",
        verbose_name="enviado por",
    )
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_validados",
        verbose_name="validado por",
    )
    validado_em = models.DateTimeField("validado em", null=True, blank=True)
    observacao = models.TextField("observacao", blank=True)
    motivo_rejeicao = models.TextField("motivo da rejeicao", blank=True)

    objects = DocumentoQuerySet.as_manager()

    class Meta:
        verbose_name = "documento"
        verbose_name_plural = "documentos"
        ordering = ("-data_emissao", "-versao")
        indexes = [
            models.Index(fields=["unidade", "tipo", "versao_corrente"]),
            models.Index(fields=["situacao", "data_vencimento"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["unidade", "tipo", "versao"], name="documento_versao_unica_por_casa_e_tipo"
            )
        ]

    def __str__(self) -> str:
        return f"{self.identificacao} ({self.unidade.nome})"

    # ------------------------------------------------------------------ calculos
    @property
    def dias_para_vencer(self) -> int | None:
        return dias_ate(self.data_vencimento)

    @property
    def status(self) -> str:
        """Status de conformidade calculado. Fonte unica de verdade."""
        return calcular_status(self)

    @property
    def prazo_protocolo_renovacao(self) -> date | None:
        """Data-limite para protocolar a renovacao e manter a validade.

        Aplica o art. 18, par. 4, da Res. CONAMA 237/1997: o protocolo feito
        com 120 dias de antecedencia prorroga a licenca ate a decisao do orgao.
        """
        if not self.data_vencimento or self.tipo.tema != TemaLegal.LICENCIAMENTO:
            return None
        dias = settings.SIGA["DIAS_PROTOCOLO_RENOVACAO_LO"]
        return self.data_vencimento - timezone.timedelta(days=dias)

    @property
    def protocolo_em_atraso(self) -> bool:
        prazo = self.prazo_protocolo_renovacao
        return bool(prazo and prazo < hoje() and self.status != StatusConformidade.VIGENTE)


class ProcessoRenovacao(UUIDModel, TimestampedModel):
    """Pasta de trabalho de uma renovação, isolada por casa."""

    class Situacao(models.TextChoices):
        PREPARACAO = "PREPARACAO", "Em preparação"
        PROTOCOLADO = "PROTOCOLADO", "Protocolado"
        PENDENCIA = "PENDENCIA", "Com pendência"
        CONCLUIDO = "CONCLUIDO", "Concluído"
        CANCELADO = "CANCELADO", "Cancelado"

    unidade = models.ForeignKey(
        "organizacao.Unidade",
        on_delete=models.PROTECT,
        related_name="processos_renovacao",
        verbose_name="casa",
    )
    tipo = models.ForeignKey(
        TipoDocumento,
        on_delete=models.PROTECT,
        related_name="processos_renovacao",
        verbose_name="documento em renovação",
    )
    documentos = models.ManyToManyField(
        Documento,
        blank=True,
        related_name="processos_renovacao",
        verbose_name="documentos já anexados",
    )
    situacao = models.CharField(
        "situação",
        max_length=12,
        choices=Situacao.choices,
        default=Situacao.PREPARACAO,
        db_index=True,
    )
    data_inicio = models.DateField("data de início", default=timezone.localdate)
    prazo = models.DateField("prazo da renovação", null=True, blank=True)
    numero_protocolo = models.CharField("número do protocolo", max_length=120, blank=True)
    observacao = models.TextField("observações", blank=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processos_renovacao_criados",
        verbose_name="criado por",
    )

    class Meta:
        verbose_name = "processo de renovação"
        verbose_name_plural = "processos de renovação"
        ordering = ("unidade__nome", "-data_inicio", "tipo__nome")
        indexes = [models.Index(fields=["unidade", "situacao"])]

    def __str__(self) -> str:
        return f"{self.tipo.nome} — {self.unidade.nome}"


class AnexoProcessoRenovacao(UUIDModel, TimestampedModel):
    """Arquivo externo anexado diretamente a um processo de renovação."""

    processo = models.ForeignKey(
        ProcessoRenovacao,
        on_delete=models.CASCADE,
        related_name="anexos_externos",
        verbose_name="processo de renovação",
    )
    arquivo = models.FileField("arquivo", upload_to=caminho_do_anexo_renovacao)
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="anexos_renovacao_enviados",
        verbose_name="enviado por",
    )

    class Meta:
        verbose_name = "anexo externo da renovação"
        verbose_name_plural = "anexos externos das renovações"
        ordering = ("criado_em",)

    def __str__(self) -> str:
        return Path(self.arquivo.name).name


def calcular_status(documento: Documento | None) -> str:
    """Deriva o status de conformidade de um documento.

    Regra unica usada pelo painel, pelo checklist, pelo relatorio de pendencias
    e pela regua de notificacoes - por isso vive fora do model, como funcao pura.
    """
    if documento is None:
        return StatusConformidade.PENDENTE
    if documento.situacao in {SituacaoDocumento.AGUARDANDO, SituacaoDocumento.RASCUNHO}:
        return StatusConformidade.EM_ANALISE
    if documento.situacao == SituacaoDocumento.REJEITADO:
        return StatusConformidade.PENDENTE
    if documento.data_vencimento is None:
        return StatusConformidade.VIGENTE

    restantes = dias_ate(documento.data_vencimento)
    if restantes is None:
        return StatusConformidade.VIGENTE
    if restantes < 0:
        return StatusConformidade.VENCIDO
    if restantes <= settings.SIGA["DIAS_CRITICO"]:
        return StatusConformidade.CRITICO
    if restantes <= settings.SIGA["DIAS_ALERTA"]:
        return StatusConformidade.AVENCER
    return StatusConformidade.VIGENTE


class Condicionante(UUIDModel, TimestampedModel):
    """Exigencia imposta pelo orgao ambiental dentro de uma licenca.

    O descumprimento e infracao administrativa autonoma (Decreto 6.514/2008),
    por isso e acompanhado separado do documento da licenca.
    """

    class Situacao(models.TextChoices):
        NAO_ATENDIDA = "NAO_ATENDIDA", "Nao atendida"
        EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
        ATENDIDA = "ATENDIDA", "Atendida"

    unidade = models.ForeignKey(
        "organizacao.Unidade",
        on_delete=models.CASCADE,
        related_name="condicionantes",
        verbose_name="casa",
    )
    licenca = models.CharField("licenca / processo", max_length=160)
    descricao = models.TextField("condicionante")
    prazo = models.DateField("prazo", null=True, blank=True)
    responsavel = models.CharField("responsavel", max_length=120)
    situacao = models.CharField(
        "situacao", max_length=15, choices=Situacao.choices, default=Situacao.NAO_ATENDIDA
    )
    evidencia = models.ForeignKey(
        Documento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="condicionantes_atendidas",
        verbose_name="documento comprobatorio",
    )

    class Meta:
        verbose_name = "condicionante"
        verbose_name_plural = "condicionantes"
        ordering = ("prazo", "unidade__nome")

    def __str__(self) -> str:
        return f"{self.unidade.nome} - {self.descricao[:60]}"

    @property
    def dias_para_prazo(self) -> int | None:
        return dias_ate(self.prazo)

    @property
    def em_atraso(self) -> bool:
        d = self.dias_para_prazo
        return d is not None and d < 0 and self.situacao != self.Situacao.ATENDIDA
