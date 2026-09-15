"""Consultas de leitura: checklist, matriz de conformidade e pendencias.

Camada sem efeito colateral. Views, API, e-mails e relatorios consomem daqui,
garantindo que todos enxerguem exatamente o mesmo numero.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from django.db.models import Prefetch

from apps.compliance.enums import VERBO_ACAO, ResponsavelExecucao, StatusConformidade
from apps.compliance.models import Documento, TipoDocumento, calcular_status
from apps.core.utils import dias_ate
from apps.organizacao.models import Unidade


@dataclass(frozen=True, slots=True)
class ItemChecklist:
    """Uma linha do checklist de uma casa."""

    unidade: Unidade
    tipo: TipoDocumento
    documento: Documento | None
    status: str

    @property
    def verbo(self) -> str:
        return VERBO_ACAO[self.status]

    @property
    def vencimento(self) -> date | None:
        return self.documento.data_vencimento if self.documento else None

    @property
    def dias(self) -> int | None:
        return dias_ate(self.vencimento)

    @property
    def da_casa(self) -> bool:
        return self.tipo.e_do_checklist_da_casa

    @property
    def atendido(self) -> bool:
        return self.status in {StatusConformidade.VIGENTE, StatusConformidade.EM_ANALISE}

    @property
    def exige_acao(self) -> bool:
        return self.status in StatusConformidade.exigem_acao()


@dataclass(frozen=True, slots=True)
class CelulaMatriz:
    """Status e destino de navegação de uma célula da matriz do painel."""

    status: str
    documento: Documento | None


@dataclass(frozen=True, slots=True)
class ResumoUnidade:
    """Placar de conformidade de uma casa."""

    unidade: Unidade
    total: int
    em_dia: int
    a_vencer: int
    critico: int
    vencido: int
    em_analise: int
    pendente: int
    itens_da_casa: int
    acao_da_casa: int

    @property
    def percentual(self) -> int:
        if not self.total:
            return 0
        regulares = self.em_dia + self.a_vencer + self.em_analise * 0.5
        return round(regulares / self.total * 100)

    @property
    def percentual_checklist(self) -> int:
        if not self.itens_da_casa:
            return 0
        return round((self.itens_da_casa - self.acao_da_casa) / self.itens_da_casa * 100)


def _documentos_correntes(unidades) -> dict[tuple[int, int], Documento]:
    """Mapa (unidade_id, tipo_id) -> versao corrente. Uma query para tudo."""
    qs = (
        Documento.objects.vigentes()
        .filter(unidade__in=unidades)
        .select_related("unidade", "tipo", "enviado_por", "validado_por")
    )
    return {(d.unidade_id, d.tipo_id): d for d in qs}


def checklist_da_unidade(unidade: Unidade) -> list[ItemChecklist]:
    """Todos os requisitos aplicaveis a uma casa, com o status de cada um."""
    tipos = TipoDocumento.objects.aplicaveis_a(unidade)
    correntes = _documentos_correntes([unidade])
    return [
        ItemChecklist(
            unidade=unidade,
            tipo=tipo,
            documento=(doc := correntes.get((unidade.pk, tipo.pk))),
            status=calcular_status(doc),
        )
        for tipo in tipos
    ]


def checklist_agrupado(unidade: Unidade) -> dict[str, list[ItemChecklist]]:
    """Checklist da casa separado por urgencia, na ordem de exibicao."""
    itens = [i for i in checklist_da_unidade(unidade) if i.da_casa]
    ordem = [
        StatusConformidade.PENDENTE,
        StatusConformidade.VENCIDO,
        StatusConformidade.CRITICO,
        StatusConformidade.AVENCER,
        StatusConformidade.EM_ANALISE,
        StatusConformidade.VIGENTE,
    ]
    return {status: [i for i in itens if i.status == status] for status in ordem}


def itens_da_consultoria(unidade: Unidade) -> list[ItemChecklist]:
    """Itens elaborados pela STX - a casa apenas acompanha."""
    return [i for i in checklist_da_unidade(unidade) if not i.da_casa]


def resumo_da_unidade(unidade: Unidade) -> ResumoUnidade:
    itens = checklist_da_unidade(unidade)
    conta = {s: 0 for s in StatusConformidade.values}
    for item in itens:
        conta[item.status] += 1
    da_casa = [i for i in itens if i.da_casa]
    return ResumoUnidade(
        unidade=unidade,
        total=len(itens),
        em_dia=conta[StatusConformidade.VIGENTE],
        a_vencer=conta[StatusConformidade.AVENCER],
        critico=conta[StatusConformidade.CRITICO],
        vencido=conta[StatusConformidade.VENCIDO],
        em_analise=conta[StatusConformidade.EM_ANALISE],
        pendente=conta[StatusConformidade.PENDENTE],
        itens_da_casa=len(da_casa),
        acao_da_casa=sum(1 for i in da_casa if i.exige_acao),
    )


def resumo_geral(unidades) -> list[ResumoUnidade]:
    """Placar de todas as casas, da mais atrasada para a mais em dia."""
    return sorted((resumo_da_unidade(u) for u in unidades), key=lambda r: r.percentual)


def matriz_conformidade(
    unidades,
) -> tuple[list[TipoDocumento], dict[int, dict[int, CelulaMatriz]]]:
    """Matriz casa x requisito para o painel."""
    tipos = list(TipoDocumento.objects.ativos())
    correntes = _documentos_correntes(unidades)
    matriz: dict[int, dict[int, CelulaMatriz]] = {}
    for unidade in unidades:
        linha: dict[int, CelulaMatriz] = {}
        for tipo in tipos:
            if not tipo.aplica_a(unidade):
                linha[tipo.pk] = CelulaMatriz(StatusConformidade.NAO_APLICAVEL, None)
            else:
                documento = correntes.get((unidade.pk, tipo.pk))
                linha[tipo.pk] = CelulaMatriz(calcular_status(documento), documento)
        matriz[unidade.pk] = linha
    return tipos, matriz


def pendencias(unidades) -> list[ItemChecklist]:
    """Tudo que falta, esta vencido ou vence em breve, por criticidade legal."""
    prioridade = {
        StatusConformidade.VENCIDO: 0,
        StatusConformidade.CRITICO: 1,
        StatusConformidade.PENDENTE: 2,
        StatusConformidade.EM_ANALISE: 3,
        StatusConformidade.AVENCER: 4,
    }
    itens: list[ItemChecklist] = []
    for unidade in unidades:
        itens.extend(i for i in checklist_da_unidade(unidade) if i.status in prioridade)
    return sorted(itens, key=lambda i: (prioridade[i.status], i.dias if i.dias is not None else 999))


def proximos_vencimentos(unidades, limite: int = 10) -> list[ItemChecklist]:
    candidatos = [i for i in pendencias(unidades) if i.dias is not None and i.dias >= 0]
    return sorted(candidatos, key=lambda i: i.dias)[:limite]


def historico_do_documento(unidade: Unidade, tipo: TipoDocumento):
    return (
        Documento.objects.ativos()
        .filter(unidade=unidade, tipo=tipo)
        .select_related("enviado_por", "validado_por")
        .order_by("-versao")
    )
