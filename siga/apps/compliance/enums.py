"""Vocabulario do dominio de conformidade."""
from __future__ import annotations

from django.db import models

UNIDADE_PREFIXO = "UNIDADE:"


def valor_unidade(codigo: str) -> str:
    """Valor persistido para uma casa escolhida dinamicamente."""
    return f"{UNIDADE_PREFIXO}{codigo}"


def codigo_unidade(valor: str) -> str | None:
    """Extrai o codigo de uma opcao de casa, quando aplicavel."""
    return valor.removeprefix(UNIDADE_PREFIXO) if valor.startswith(UNIDADE_PREFIXO) else None


class Aplicabilidade(models.TextChoices):
    """Regra que decide se um requisito vale para determinada casa."""

    TODAS = "TODAS", "Todas as casas"
    OFICINA = "OFICINA", "Somente casas com oficina"
    POCO = "POCO", "Somente casas com captacao propria"
    POSTO = "POSTO", "Somente casa em area de posto"
    IMOVEL_TERCEIRO = "IMOVEL_TERCEIRO", "Somente casas em imovel de terceiro"


class ResponsavelExecucao(models.TextChoices):
    """Quem executa o item. Define para quem vai a cobranca por e-mail."""

    CASA = "CASA", "Casa"
    MCM_STX = "MCM_STX", "MCM + STX"
    MCM = "MCM", "MCM (matriz)"
    STX = "STX", "STX Engenharia"
    STX_ELABORA = "STX_ELABORA", "STX elabora"

    @classmethod
    def da_casa(cls) -> frozenset[str]:
        """Responsaveis cujo item entra no checklist da coordenadora."""
        return frozenset(
            {
                cls.CASA,
                cls.MCM_STX,
                cls.MCM,
            }
        )


class TemaLegal(models.TextChoices):
    CONDICIONANTES = "CONDICIONANTES", "Condicionantes"
    LICENCIAMENTO = "LICENCIAMENTO", "Licenciamento"
    HIDRICOS = "HIDRICOS", "Recursos hidricos"
    FEDERAL = "FEDERAL", "Conformidade federal"
    RESIDUOS = "RESIDUOS", "Residuos"
    EFLUENTES = "EFLUENTES", "Efluentes"
    SOLO = "SOLO", "Solo e agua subterranea"
    POSTO = "POSTO", "Posto de combustivel"
    MONITORAMENTO = "MONITORAMENTO", "Monitoramento"
    SGA = "SGA", "Gestao / SGA"
    EMERGENCIA = "EMERGENCIA", "Emergencia"
    SEGURANCA = "SEGURANCA", "Seguranca"
    SST = "SST", "Saude e seguranca do trabalho"
    TERCEIROS = "TERCEIROS", "Terceiros"


class SituacaoDocumento(models.TextChoices):
    """Estado do fluxo de aprovacao - decidido por pessoas."""

    RASCUNHO = "RASCUNHO", "Rascunho"
    AGUARDANDO = "AGUARDANDO", "Aguardando validacao"
    VALIDADO = "VALIDADO", "Validado"
    REJEITADO = "REJEITADO", "Rejeitado"


class StatusConformidade(models.TextChoices):
    """Estado calculado a partir das datas - nunca editado a mao."""

    VIGENTE = "VIGENTE", "Em dia"
    AVENCER = "AVENCER", "A vencer"
    CRITICO = "CRITICO", "Critico"
    VENCIDO = "VENCIDO", "Vencido"
    EM_ANALISE = "EM_ANALISE", "Em analise"
    PENDENTE = "PENDENTE", "Nao enviado"
    NAO_APLICAVEL = "NAO_APLICAVEL", "Nao aplicavel"

    @classmethod
    def regulares(cls) -> frozenset[str]:
        """Status que contam como conformidade atendida."""
        return frozenset({cls.VIGENTE, cls.AVENCER})

    @classmethod
    def exigem_acao(cls) -> frozenset[str]:
        return frozenset({cls.PENDENTE, cls.VENCIDO, cls.CRITICO})


#: Rotulo em linguagem direta usado no checklist da coordenadora.
VERBO_ACAO = {
    StatusConformidade.PENDENTE: "Enviar / providenciar",
    StatusConformidade.VENCIDO: "Renovar e reenviar",
    StatusConformidade.CRITICO: "Renovar agora",
    StatusConformidade.AVENCER: "Preparar renovacao",
    StatusConformidade.EM_ANALISE: "Aguardando validacao da STX",
    StatusConformidade.VIGENTE: "Em dia",
    StatusConformidade.NAO_APLICAVEL: "Nao aplicavel",
}
