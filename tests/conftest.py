"""Fixtures compartilhadas dos testes."""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model

from apps.compliance.enums import (
    Aplicabilidade,
    ResponsavelExecucao,
    SituacaoDocumento,
    TemaLegal,
)
from apps.compliance.models import Documento, TipoDocumento
from apps.organizacao.models import Unidade

Usuario = get_user_model()


@pytest.fixture
def hoje() -> date:
    from apps.core.utils import hoje as _hoje

    return _hoje()


@pytest.fixture
def casa(db) -> Unidade:
    return Unidade.objects.create(
        codigo="U9", nome="Casa de Teste", uf="MA", municipio="Sao Luis",
        cnpj="00.000.000/0001-00", tem_oficina=True, tem_poco=True, opera_em_posto=False,
        responsavel_nome="Coordenadora", responsavel_email="casa@mcm.com.br",
    )


@pytest.fixture
def casa_sem_oficina(db) -> Unidade:
    return Unidade.objects.create(
        codigo="U8", nome="Casa Sem Oficina", uf="MA", municipio="Balsas",
        cnpj="00.000.000/0002-00", tem_oficina=False, tem_poco=False, opera_em_posto=False,
        responsavel_email="semoficina@mcm.com.br",
    )


def _tipo(codigo: str, **extra) -> TipoDocumento:
    padrao = dict(
        nome=f"Documento {codigo}", tema=TemaLegal.LICENCIAMENTO, periodicidade_meses=12,
        dias_alerta=90, aplicabilidade=Aplicabilidade.TODAS,
        responsavel_execucao=ResponsavelExecucao.CASA,
        base_legal="Lei de teste", instrucao="Enviar o documento.",
    )
    padrao.update(extra)
    return TipoDocumento.objects.create(codigo=codigo, **padrao)


@pytest.fixture
def tipo_licenca(db) -> TipoDocumento:
    return _tipo("TX1", periodicidade_meses=48, dias_alerta=120)


@pytest.fixture
def tipo_oficina(db) -> TipoDocumento:
    return _tipo("TX2", aplicabilidade=Aplicabilidade.OFICINA, tema=TemaLegal.EFLUENTES)


@pytest.fixture
def tipo_stx(db) -> TipoDocumento:
    return _tipo("TX3", responsavel_execucao=ResponsavelExecucao.STX_ELABORA)


@pytest.fixture
def coordenadora(db, casa) -> Usuario:
    return Usuario.objects.create_user(
        username="coord", email="coord@mcm.com.br", password="x",
        nome_completo="Coordenadora", perfil="UNIDADE", unidade=casa,
    )


@pytest.fixture
def consultoria(db) -> Usuario:
    return Usuario.objects.create_user(
        username="stx", email="stx@teste.com", password="x",
        nome_completo="STX Engenharia", perfil="CONSULTORIA",
    )


@pytest.fixture
def auditor(db) -> Usuario:
    return Usuario.objects.create_user(
        username="aud", email="aud@mcm.com.br", password="x",
        nome_completo="Auditor", perfil="AUDITOR",
    )


@pytest.fixture
def documento_valido(db, casa, tipo_licenca, hoje) -> Documento:
    return Documento.objects.create(
        unidade=casa, tipo=tipo_licenca, identificacao="LO 001/2024",
        data_emissao=hoje - timedelta(days=365), data_vencimento=hoje + timedelta(days=400),
        situacao=SituacaoDocumento.VALIDADO,
    )
