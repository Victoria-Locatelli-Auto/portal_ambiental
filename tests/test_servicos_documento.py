"""Envio, versionamento e validacao de documentos."""
from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.compliance import services
from apps.compliance.enums import SituacaoDocumento, StatusConformidade
from apps.compliance.models import Documento
from apps.core.models import LogAuditoria

pytestmark = pytest.mark.django_db


def test_envio_cria_documento_em_analise(casa, tipo_licenca, coordenadora, hoje):
    doc = services.enviar_documento(
        unidade=casa, tipo=tipo_licenca, identificacao="LO 123",
        data_emissao=hoje, usuario=coordenadora,
    )
    assert doc.situacao == SituacaoDocumento.AGUARDANDO
    assert doc.status == StatusConformidade.EM_ANALISE
    assert doc.versao == 1
    assert doc.versao_corrente is True


def test_vencimento_calculado_pela_periodicidade(casa, tipo_licenca, coordenadora, hoje):
    from apps.core.utils import somar_meses

    doc = services.enviar_documento(
        unidade=casa, tipo=tipo_licenca, identificacao="LO",
        data_emissao=hoje, usuario=coordenadora,
    )
    assert doc.data_vencimento == somar_meses(hoje, 48)


def test_sem_data_validade_impede_calculo_automatico(casa, tipo_licenca, coordenadora, hoje):
    doc = services.enviar_documento(
        unidade=casa,
        tipo=tipo_licenca,
        identificacao="Documento permanente",
        data_emissao=hoje,
        usuario=coordenadora,
        sem_data_validade=True,
    )
    assert doc.data_vencimento is None


def test_novo_envio_versiona_e_arquiva_o_anterior(casa, tipo_licenca, coordenadora, hoje):
    primeiro = services.enviar_documento(
        unidade=casa, tipo=tipo_licenca, identificacao="v1",
        data_emissao=hoje - timedelta(days=10), usuario=coordenadora,
    )
    segundo = services.enviar_documento(
        unidade=casa, tipo=tipo_licenca, identificacao="v2",
        data_emissao=hoje, usuario=coordenadora,
    )
    primeiro.refresh_from_db()
    assert primeiro.versao_corrente is False
    assert segundo.versao == 2
    assert Documento.objects.vigentes().filter(unidade=casa, tipo=tipo_licenca).count() == 1
    assert Documento.objects.filter(unidade=casa, tipo=tipo_licenca).count() == 2


def test_auditor_nao_pode_enviar(casa, tipo_licenca, auditor, hoje):
    with pytest.raises(PermissionDenied):
        services.enviar_documento(
            unidade=casa, tipo=tipo_licenca, identificacao="x",
            data_emissao=hoje, usuario=auditor,
        )


def test_coordenadora_nao_envia_para_outra_casa(casa_sem_oficina, tipo_licenca, coordenadora, hoje):
    with pytest.raises(PermissionDenied):
        services.enviar_documento(
            unidade=casa_sem_oficina, tipo=tipo_licenca, identificacao="x",
            data_emissao=hoje, usuario=coordenadora,
        )


def test_nao_envia_requisito_inaplicavel(casa_sem_oficina, tipo_oficina, consultoria, hoje):
    with pytest.raises(ValidationError):
        services.enviar_documento(
            unidade=casa_sem_oficina, tipo=tipo_oficina, identificacao="x",
            data_emissao=hoje, usuario=consultoria,
        )


def test_emissao_futura_e_rejeitada(casa, tipo_licenca, coordenadora, hoje):
    with pytest.raises(ValidationError):
        services.enviar_documento(
            unidade=casa, tipo=tipo_licenca, identificacao="x",
            data_emissao=hoje + timedelta(days=1), usuario=coordenadora,
        )


def test_apenas_consultoria_valida(casa, tipo_licenca, coordenadora, consultoria, hoje):
    doc = services.enviar_documento(
        unidade=casa, tipo=tipo_licenca, identificacao="x",
        data_emissao=hoje, usuario=coordenadora,
    )
    with pytest.raises(PermissionDenied):
        services.validar_documento(documento=doc, usuario=coordenadora)

    services.validar_documento(documento=doc, usuario=consultoria)
    doc.refresh_from_db()
    assert doc.situacao == SituacaoDocumento.VALIDADO
    assert doc.validado_por == consultoria


def test_rejeicao_exige_motivo(casa, tipo_licenca, coordenadora, consultoria, hoje):
    doc = services.enviar_documento(
        unidade=casa, tipo=tipo_licenca, identificacao="x",
        data_emissao=hoje, usuario=coordenadora,
    )
    with pytest.raises(ValidationError):
        services.rejeitar_documento(documento=doc, usuario=consultoria, motivo="  ")


def test_envio_grava_trilha_de_auditoria(casa, tipo_licenca, coordenadora, hoje):
    services.enviar_documento(
        unidade=casa, tipo=tipo_licenca, identificacao="x",
        data_emissao=hoje, usuario=coordenadora,
    )
    assert LogAuditoria.objects.filter(acao=LogAuditoria.Acao.ENVIO).exists()
