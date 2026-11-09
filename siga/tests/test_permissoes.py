"""Escopo de dados por perfil."""
import pytest

pytestmark = pytest.mark.django_db


def test_coordenadora_ve_apenas_a_propria_casa(coordenadora, casa, casa_sem_oficina):
    visiveis = list(coordenadora.unidades_visiveis())
    assert visiveis == [casa]
    assert coordenadora.pode_acessar(casa) is True
    assert coordenadora.pode_acessar(casa_sem_oficina) is False


def test_consultoria_ve_todas(consultoria, casa, casa_sem_oficina):
    assert consultoria.unidades_visiveis().count() == 2
    assert consultoria.escopo_global is True


def test_auditor_e_somente_leitura(auditor):
    assert auditor.somente_leitura is True
    assert auditor.pode_validar is False


def test_apenas_consultoria_e_admin_validam(consultoria, coordenadora, auditor):
    assert consultoria.pode_validar is True
    assert coordenadora.pode_validar is False
    assert auditor.pode_validar is False
