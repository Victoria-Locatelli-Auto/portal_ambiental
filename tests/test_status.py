"""Motor de status de conformidade - regra central do sistema."""
from datetime import timedelta

import pytest

from apps.compliance.enums import SituacaoDocumento, StatusConformidade
from apps.compliance.models import Documento, calcular_status

pytestmark = pytest.mark.django_db


def _doc(casa, tipo, hoje, dias, situacao=SituacaoDocumento.VALIDADO):
    return Documento(
        unidade=casa, tipo=tipo, identificacao="X",
        data_emissao=hoje - timedelta(days=30),
        data_vencimento=hoje + timedelta(days=dias) if dias is not None else None,
        situacao=situacao,
    )


def test_sem_documento_e_pendente():
    assert calcular_status(None) == StatusConformidade.PENDENTE


@pytest.mark.parametrize(
    ("dias", "esperado"),
    [
        (-1, StatusConformidade.VENCIDO),
        (0, StatusConformidade.CRITICO),
        (30, StatusConformidade.CRITICO),
        (31, StatusConformidade.AVENCER),
        (90, StatusConformidade.AVENCER),
        (91, StatusConformidade.VIGENTE),
        (None, StatusConformidade.VIGENTE),
    ],
)
def test_faixas_de_status(casa, tipo_licenca, hoje, dias, esperado):
    assert calcular_status(_doc(casa, tipo_licenca, hoje, dias)) == esperado


def test_aguardando_validacao_fica_em_analise(casa, tipo_licenca, hoje):
    doc = _doc(casa, tipo_licenca, hoje, -100, SituacaoDocumento.AGUARDANDO)
    assert calcular_status(doc) == StatusConformidade.EM_ANALISE


def test_rejeitado_volta_a_ser_pendencia(casa, tipo_licenca, hoje):
    doc = _doc(casa, tipo_licenca, hoje, 400, SituacaoDocumento.REJEITADO)
    assert calcular_status(doc) == StatusConformidade.PENDENTE


def test_prazo_de_protocolo_da_licenca(documento_valido):
    """CONAMA 237/1997, art. 18, par. 4: 120 dias antes do vencimento."""
    esperado = documento_valido.data_vencimento - timedelta(days=120)
    assert documento_valido.prazo_protocolo_renovacao == esperado
