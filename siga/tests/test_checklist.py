"""Checklist por casa e placar de conformidade."""
import pytest

from apps.compliance import services
from apps.compliance.enums import StatusConformidade
from apps.compliance.selectors import (
    checklist_agrupado,
    checklist_da_unidade,
    itens_da_consultoria,
    pendencias,
    resumo_da_unidade,
)

pytestmark = pytest.mark.django_db


def test_checklist_traz_apenas_requisitos_aplicaveis(casa_sem_oficina, tipo_licenca, tipo_oficina):
    codigos = {i.tipo.codigo for i in checklist_da_unidade(casa_sem_oficina)}
    assert tipo_licenca.codigo in codigos
    assert tipo_oficina.codigo not in codigos


def test_separa_itens_da_casa_dos_da_consultoria(casa, tipo_licenca, tipo_stx):
    da_casa = {i.tipo.codigo for i in checklist_da_unidade(casa) if i.da_casa}
    da_stx = {i.tipo.codigo for i in itens_da_consultoria(casa)}
    assert tipo_licenca.codigo in da_casa
    assert tipo_stx.codigo in da_stx
    assert not da_casa & da_stx


def test_item_enviado_sai_do_grupo_pendente(casa, tipo_licenca, coordenadora, hoje):
    grupos = checklist_agrupado(casa)
    assert any(i.tipo == tipo_licenca for i in grupos[StatusConformidade.PENDENTE])

    services.enviar_documento(
        unidade=casa, tipo=tipo_licenca, identificacao="LO",
        data_emissao=hoje, usuario=coordenadora,
    )

    grupos = checklist_agrupado(casa)
    assert not any(i.tipo == tipo_licenca for i in grupos[StatusConformidade.PENDENTE])
    assert any(i.tipo == tipo_licenca for i in grupos[StatusConformidade.EM_ANALISE])


def test_resumo_conta_por_status(casa, tipo_licenca, tipo_oficina, tipo_stx):
    resumo = resumo_da_unidade(casa)
    assert resumo.total == 3
    assert resumo.pendente == 3
    assert resumo.percentual == 0
    assert resumo.itens_da_casa == 2  # tipo_stx nao entra
    assert resumo.acao_da_casa == 2


def test_percentual_sobe_apos_validacao(casa, tipo_licenca, coordenadora, consultoria, hoje):
    antes = resumo_da_unidade(casa).percentual
    doc = services.enviar_documento(
        unidade=casa, tipo=tipo_licenca, identificacao="LO",
        data_emissao=hoje, usuario=coordenadora,
    )
    services.validar_documento(documento=doc, usuario=consultoria)
    assert resumo_da_unidade(casa).percentual > antes


def test_pendencias_ordenadas_por_criticidade(casa, casa_sem_oficina, tipo_licenca):
    itens = pendencias([casa, casa_sem_oficina])
    assert all(i.status in StatusConformidade.exigem_acao() for i in itens)
    assert len(itens) > 0
