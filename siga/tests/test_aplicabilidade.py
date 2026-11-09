"""Regras que decidem quais requisitos valem para cada casa."""
import pytest

from apps.compliance.enums import Aplicabilidade, valor_unidade
from apps.compliance.models import TipoDocumento

pytestmark = pytest.mark.django_db


def test_requisito_de_oficina_nao_vale_para_casa_sem_oficina(casa, casa_sem_oficina, tipo_oficina):
    assert tipo_oficina.aplica_a(casa) is True
    assert tipo_oficina.aplica_a(casa_sem_oficina) is False


def test_queryset_filtra_por_caracteristica(casa_sem_oficina, tipo_licenca, tipo_oficina):
    codigos = set(
        TipoDocumento.objects.aplicaveis_a(casa_sem_oficina).values_list("codigo", flat=True)
    )
    assert tipo_licenca.codigo in codigos
    assert tipo_oficina.codigo not in codigos


def test_requisito_de_posto_so_para_casa_em_posto(casa, tipo_licenca):
    tipo_licenca.aplicabilidade = Aplicabilidade.POSTO
    assert tipo_licenca.aplica_a(casa) is False
    casa.opera_em_posto = True
    assert tipo_licenca.aplica_a(casa) is True


def test_requisito_de_unidade_especifica_aparece_somente_nela(
    casa, casa_sem_oficina, tipo_licenca
):
    casa.codigo = "U1"
    casa.save(update_fields=["codigo"])
    casa_sem_oficina.codigo = "U3"
    casa_sem_oficina.save(update_fields=["codigo"])
    tipo_licenca.aplicabilidade = valor_unidade(casa.codigo)
    tipo_licenca.save(update_fields=["aplicabilidade"])

    assert tipo_licenca.aplica_a(casa) is True
    assert tipo_licenca.aplica_a(casa_sem_oficina) is False
    assert TipoDocumento.objects.aplicaveis_a(casa).filter(pk=tipo_licenca.pk).exists()
    assert not TipoDocumento.objects.aplicaveis_a(casa_sem_oficina).filter(
        pk=tipo_licenca.pk
    ).exists()


def test_requisito_pode_ser_aplicavel_a_mais_de_uma_unidade(
    casa, casa_sem_oficina, tipo_licenca
):
    casa.codigo = "U1"
    casa.save(update_fields=["codigo"])
    casa_sem_oficina.codigo = "U2"
    casa_sem_oficina.save(update_fields=["codigo"])
    tipo_licenca.aplicabilidade = ",".join(
        [valor_unidade(casa.codigo), valor_unidade(casa_sem_oficina.codigo)]
    )
    tipo_licenca.save(update_fields=["aplicabilidade"])

    assert tipo_licenca.aplica_a(casa)
    assert tipo_licenca.aplica_a(casa_sem_oficina)
    assert TipoDocumento.objects.aplicaveis_a(casa).filter(pk=tipo_licenca.pk).exists()
    assert TipoDocumento.objects.aplicaveis_a(casa_sem_oficina).filter(
        pk=tipo_licenca.pk
    ).exists()


def test_calculo_de_vencimento_por_periodicidade(tipo_licenca, hoje):
    from apps.core.utils import somar_meses

    assert tipo_licenca.calcular_vencimento(hoje) == somar_meses(hoje, 48)


def test_documento_por_evento_nao_tem_vencimento(tipo_licenca, hoje):
    tipo_licenca.periodicidade_meses = 0
    assert tipo_licenca.calcular_vencimento(hoje) is None
