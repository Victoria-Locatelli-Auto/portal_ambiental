"""Regua de notificacoes: alertas diarios, consolidacao e idempotencia."""
from datetime import timedelta

import pytest
from django.core import mail
from django.urls import reverse

from apps.compliance import services as compliance
from apps.compliance.enums import SituacaoDocumento
from apps.compliance.models import Documento
from apps.notificacoes import services
from apps.notificacoes.models import (
    ModeloEmail,
    Notificacao,
    NotificacaoSistema,
    TipoNotificacao,
)

pytestmark = pytest.mark.django_db


def _documento(casa, tipo, hoje, dias):
    return Documento.objects.create(
        unidade=casa, tipo=tipo, identificacao="LO 1",
        data_emissao=hoje - timedelta(days=10),
        data_vencimento=hoje + timedelta(days=dias),
        situacao=SituacaoDocumento.VALIDADO,
    )


def test_alerta_disparado_diariamente_dentro_da_antecedencia(casa, tipo_licenca, hoje):
    _documento(casa, tipo_licenca, hoje, 30)
    mensagens = services.montar_alertas(casa)
    alertas = [m for m in mensagens if m.tipo == TipoNotificacao.ALERTA]
    assert len(alertas) == 1
    assert "vence em 30 dias" in alertas[0].assunto


def test_alerta_tambem_dispara_fora_dos_antigos_marcos(casa, tipo_licenca, hoje):
    _documento(casa, tipo_licenca, hoje, 29)
    alertas = [m for m in services.montar_alertas(casa) if m.tipo == TipoNotificacao.ALERTA]
    assert len(alertas) == 1
    assert "vence em 29 dias" in alertas[0].assunto


def test_alerta_tem_chave_diferente_em_cada_dia(casa, tipo_licenca, hoje):
    _documento(casa, tipo_licenca, hoje, 30)
    hoje_msg = services.montar_alertas(casa, hoje)[0]
    amanha_msg = services.montar_alertas(casa, hoje + timedelta(days=1))[0]
    assert hoje_msg.chave != amanha_msg.chave
    assert hoje_msg.gatilho_dias == 30
    assert amanha_msg.gatilho_dias == 29


def test_sem_alerta_fora_da_antecedencia_do_tipo(casa, tipo_oficina, hoje):
    """tipo_oficina alerta com 90 dias; a 200 dias nao deve avisar."""
    _documento(casa, tipo_oficina, hoje, 200)
    alertas = [m for m in services.montar_alertas(casa) if m.tipo == TipoNotificacao.ALERTA]
    assert alertas == []


def test_vencido_copia_gestao_e_escalona_para_diretoria(casa, tipo_licenca, hoje, settings):
    _documento(casa, tipo_licenca, hoje, -40)
    vencidos = [m for m in services.montar_alertas(casa) if m.tipo == TipoNotificacao.VENCIDO]
    assert len(vencidos) == 1
    assert settings.SIGA["EMAIL_DIRETORIA"] in vencidos[0].copias
    assert "VENCIDO ha 40 dias" in vencidos[0].assunto


def test_vencido_recente_nao_escalona(casa, tipo_licenca, hoje, settings):
    _documento(casa, tipo_licenca, hoje, -5)
    vencidos = [m for m in services.montar_alertas(casa) if m.tipo == TipoNotificacao.VENCIDO]
    assert settings.SIGA["EMAIL_DIRETORIA"] not in vencidos[0].copias


def test_cobranca_e_unica_e_consolidada(casa, tipo_licenca, tipo_oficina):
    mensagem = services.montar_cobranca(casa)
    assert mensagem is not None
    assert mensagem.contexto["total"] == 2
    assert "2 documento(s) a enviar" in mensagem.assunto


def test_cobranca_ignora_itens_da_consultoria(casa, tipo_stx):
    assert services.montar_cobranca(casa) is None


def test_cobranca_some_apos_envio(casa, tipo_licenca, coordenadora, hoje):
    assert services.montar_cobranca(casa) is not None
    compliance.enviar_documento(
        unidade=casa, tipo=tipo_licenca, identificacao="LO",
        data_emissao=hoje, usuario=coordenadora,
    )
    assert services.montar_cobranca(casa) is None


def test_despacho_envia_email_e_registra(casa, tipo_licenca, hoje):
    _documento(casa, tipo_licenca, hoje, 30)
    mensagem = services.montar_alertas(casa)[0]
    notificacao = services.despachar(mensagem)
    assert notificacao.situacao == Notificacao.Situacao.ENVIADA
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [casa.responsavel_email]


def test_despacho_cria_alertas_internos_por_usuario_autorizado(
    casa, tipo_licenca, hoje, coordenadora, consultoria
):
    documento = _documento(casa, tipo_licenca, hoje, 30)
    notificacao = services.despachar(services.montar_alertas(casa)[0])
    avisos = NotificacaoSistema.objects.filter(origem_email=notificacao)
    assert set(avisos.values_list("usuario_id", flat=True)) == {
        coordenadora.pk,
        consultoria.pk,
    }
    assert avisos.filter(documento=documento, lida_em__isnull=True).count() == 2


def test_usuario_sem_preferencia_nao_recebe_alerta_interno(
    casa, tipo_licenca, hoje, coordenadora
):
    coordenadora.recebe_notificacoes = False
    coordenadora.save(update_fields=["recebe_notificacoes"])
    _documento(casa, tipo_licenca, hoje, 30)
    services.despachar(services.montar_alertas(casa)[0])
    assert not NotificacaoSistema.objects.filter(usuario=coordenadora).exists()


def test_central_lista_e_marca_notificacao_como_lida(
    client, casa, tipo_licenca, hoje, coordenadora
):
    _documento(casa, tipo_licenca, hoje, 30)
    services.despachar(services.montar_alertas(casa)[0])
    aviso = NotificacaoSistema.objects.get(usuario=coordenadora)
    client.force_login(coordenadora)

    resposta = client.get(reverse("notificacoes:lista"))
    assert resposta.status_code == 200
    assert aviso.titulo.encode() in resposta.content
    assert resposta.context["notificacoes_nao_lidas"] == 1

    resposta = client.get(reverse("notificacoes:abrir", args=[aviso.uuid]))
    assert resposta.status_code == 302
    aviso.refresh_from_db()
    assert aviso.lida_em is not None


def test_idempotencia_impede_reenvio(casa, tipo_licenca, hoje):
    _documento(casa, tipo_licenca, hoje, 30)
    mensagem = services.montar_alertas(casa)[0]
    assert services.despachar(mensagem) is not None
    assert services.despachar(mensagem) is None
    assert len(mail.outbox) == 1


def test_previa_nao_persiste_nada(casa, tipo_licenca, hoje):
    _documento(casa, tipo_licenca, hoje, 30)
    mensagens = services.previa()
    assert len(mensagens) > 0
    assert Notificacao.objects.count() == 0
    assert mail.outbox == []


def test_despacho_usa_texto_configurado(casa, tipo_licenca, hoje):
    _documento(casa, tipo_licenca, hoje, 30)
    ModeloEmail.objects.update_or_create(
        tipo=TipoNotificacao.ALERTA,
        defaults={
            "assunto": "Alerta {{ unidade.nome }}",
            "corpo": "Documento: {{ item.tipo.nome }} — faltam {{ dias_restantes }} dias.",
            "ativo": True,
        },
    )
    services.despachar(services.montar_alertas(casa)[0])
    assert mail.outbox[0].subject == f"Alerta {casa.nome}"
    assert "faltam 30 dias" in mail.outbox[0].body


def test_admin_edita_modelo_e_envia_email_de_teste(client, consultoria):
    consultoria.perfil = "ADMIN"
    consultoria.save(update_fields=["perfil"])
    modelo, _ = ModeloEmail.objects.update_or_create(
        tipo=TipoNotificacao.ALERTA,
        defaults={"assunto": "Assunto antigo", "corpo": "Corpo antigo"},
    )
    client.force_login(consultoria)
    resposta = client.post(
        reverse("administracao:modelo_email_editar", args=[modelo.pk]),
        {"assunto": "Novo {{ unidade.nome }}", "corpo": "Novo conteúdo", "ativo": "on"},
    )
    assert resposta.status_code == 302
    modelo.refresh_from_db()
    assert modelo.assunto == "Novo {{ unidade.nome }}"

    resposta = client.post(
        reverse("administracao:modelos_email"),
        {"destinatario": "teste@mcm.com.br"},
    )
    assert resposta.status_code == 302
    assert mail.outbox[-1].to == ["teste@mcm.com.br"]
