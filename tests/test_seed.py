"""O seed carrega os dados reais das auditorias e o sistema responde."""
import pytest
from django.core.management import call_command

from apps.auditoria.models import NaoConformidade, RelatorioAuditoria
from apps.compliance.models import Documento, TipoDocumento
from apps.compliance.selectors import resumo_geral
from apps.organizacao.models import Unidade

pytestmark = pytest.mark.django_db


@pytest.fixture
def carregado():
    call_command("seed_siga", verbosity=0)


def test_carrega_as_sete_casas(carregado):
    assert Unidade.objects.count() == 7
    assert Unidade.objects.get(codigo="U4").nome == "Imperatriz"


def test_catalogo_legal_completo(carregado):
    assert TipoDocumento.objects.count() == 32


def test_imperatriz_e_a_unica_com_licenca_propria(carregado):
    licencas = Documento.objects.vigentes().filter(tipo__codigo="T01")
    assert licencas.count() == 1
    assert licencas.first().unidade.codigo == "U4"


def test_balsas_sem_oficina_nao_exige_sao(carregado):
    balsas = Unidade.objects.get(codigo="U3")
    assert balsas.tem_oficina is False
    aplicaveis = TipoDocumento.objects.aplicaveis_a(balsas).values_list("codigo", flat=True)
    assert "T20" not in aplicaveis  # SAO


def test_posto_roma_exige_estanqueidade(carregado):
    roma = Unidade.objects.get(codigo="U7")
    aplicaveis = TipoDocumento.objects.aplicaveis_a(roma).values_list("codigo", flat=True)
    assert "T23" in aplicaveis


def test_relatorio_de_teresina_marcado_como_nao_recebido(carregado):
    relatorio = RelatorioAuditoria.objects.get(unidade__codigo="U6")
    assert relatorio.recebido is False


def test_nao_conformidades_criticas_das_auditorias(carregado):
    criticas = NaoConformidade.objects.criticas()
    assert criticas.count() >= 5
    assert criticas.filter(unidade__codigo="U5").exists()  # uso do solo do Galpao


def test_seed_e_idempotente(carregado):
    call_command("seed_siga", verbosity=0)
    assert Unidade.objects.count() == 7
    assert TipoDocumento.objects.count() == 32


def test_resumo_geral_calcula_para_todas(carregado):
    resumos = resumo_geral(Unidade.objects.ativos())
    assert len(resumos) == 7
    assert all(r.total > 0 for r in resumos)
