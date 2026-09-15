"""Fluxos dos processos de renovação documental."""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.compliance import services
from apps.compliance.models import AnexoProcessoRenovacao, ProcessoRenovacao

pytestmark = pytest.mark.django_db


def test_aba_renovacoes_separa_casas_conforme_escopo(
    client, coordenadora, casa, casa_sem_oficina
):
    client.force_login(coordenadora)
    resposta = client.get(reverse("compliance:renovacoes"))
    assert resposta.status_code == 200
    assert "Processo de Emissão/ Renovação" in resposta.content.decode()
    assert casa.nome.encode() in resposta.content
    assert casa_sem_oficina.nome.encode() not in resposta.content
    assert reverse("compliance:renovacao_criar", args=[casa.codigo]).encode() in resposta.content


def test_cria_processo_com_documento_ja_anexado_da_mesma_casa(
    client, coordenadora, casa, tipo_licenca, hoje
):
    documento = services.enviar_documento(
        unidade=casa,
        tipo=tipo_licenca,
        identificacao="Licença usada na renovação",
        data_emissao=hoje,
        usuario=coordenadora,
    )
    client.force_login(coordenadora)
    resposta = client.post(
        reverse("compliance:renovacao_criar", args=[casa.codigo]),
        {
            "tipo": tipo_licenca.pk,
            "situacao": ProcessoRenovacao.Situacao.PREPARACAO,
            "data_inicio": hoje.isoformat(),
            "prazo": "",
            "numero_protocolo": "",
            "documentos": [documento.pk],
            "observacao": "Separar documentos para protocolo.",
        },
    )
    assert resposta.status_code == 302
    processo = ProcessoRenovacao.objects.get(unidade=casa, tipo=tipo_licenca)
    assert list(processo.documentos.all()) == [documento]
    assert processo.criado_por == coordenadora


def test_nao_permite_documento_de_outra_casa_no_processo(
    client, coordenadora, casa, casa_sem_oficina, tipo_licenca, hoje
):
    documento_outra_casa = services.enviar_documento(
        unidade=casa_sem_oficina,
        tipo=tipo_licenca,
        identificacao="Documento de outra casa",
        data_emissao=hoje,
        usuario=coordenadora.__class__.objects.create_user(
            username="outra-casa",
            email="outra-casa@mcm.com.br",
            password="senha-teste",
            nome_completo="Outra Casa",
            perfil=coordenadora.perfil,
            unidade=casa_sem_oficina,
        ),
    )
    client.force_login(coordenadora)
    resposta = client.post(
        reverse("compliance:renovacao_criar", args=[casa.codigo]),
        {
            "tipo": tipo_licenca.pk,
            "situacao": ProcessoRenovacao.Situacao.PREPARACAO,
            "data_inicio": hoje.isoformat(),
            "documentos": [documento_outra_casa.pk],
        },
    )
    assert resposta.status_code == 200
    assert not ProcessoRenovacao.objects.exists()


def test_auditor_nao_cria_processo_de_renovacao(client, auditor, casa):
    client.force_login(auditor)
    resposta = client.get(reverse("compliance:renovacao_criar", args=[casa.codigo]))
    assert resposta.status_code == 403


def test_cria_processo_com_varios_anexos_externos(
    client, coordenadora, casa, tipo_licenca, hoje, settings, tmp_path
):
    settings.MEDIA_ROOT = tmp_path
    client.force_login(coordenadora)
    resposta = client.post(
        reverse("compliance:renovacao_criar", args=[casa.codigo]),
        {
            "tipo": tipo_licenca.pk,
            "situacao": ProcessoRenovacao.Situacao.PREPARACAO,
            "data_inicio": hoje.isoformat(),
            "prazo": "",
            "numero_protocolo": "",
            "observacao": "Documentação recebida externamente.",
            "anexos_externos": [
                SimpleUploadedFile("protocolo.pdf", b"arquivo 1", "application/pdf"),
                SimpleUploadedFile("comprovante.jpg", b"arquivo 2", "image/jpeg"),
            ],
        },
    )

    assert resposta.status_code == 302
    processo = ProcessoRenovacao.objects.get(unidade=casa, tipo=tipo_licenca)
    assert processo.anexos_externos.count() == 2
    assert set(
        processo.anexos_externos.values_list("enviado_por", flat=True)
    ) == {coordenadora.pk}


def test_download_do_anexo_para_usuario_autorizado(
    client, coordenadora, auditor, casa, tipo_licenca, hoje, settings, tmp_path
):
    settings.MEDIA_ROOT = tmp_path
    processo = ProcessoRenovacao.objects.create(
        unidade=casa,
        tipo=tipo_licenca,
        data_inicio=hoje,
        criado_por=coordenadora,
    )
    anexo = AnexoProcessoRenovacao.objects.create(
        processo=processo,
        arquivo=SimpleUploadedFile("externo.pdf", b"conteudo", "application/pdf"),
        enviado_por=coordenadora,
    )

    client.force_login(coordenadora)
    resposta = client.get(
        reverse("compliance:renovacao_anexo_baixar", args=[anexo.uuid])
    )
    assert resposta.status_code == 200
    assert resposta["Content-Disposition"].startswith("attachment;")

    client.force_login(auditor)
    resposta = client.get(
        reverse("compliance:renovacao_anexo_baixar", args=[anexo.uuid])
    )
    assert resposta.status_code == 200
