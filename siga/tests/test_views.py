"""Fluxo ponta a ponta pelas telas."""
from datetime import timedelta
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_painel_exige_login(client):
    resposta = client.get(reverse("dashboard:painel"))
    assert resposta.status_code == 302
    assert "/entrar/" in resposta.url


def test_login_exibe_foto_da_filial_e_identidade_verde(client):
    resposta = client.get(reverse("login"))
    assert resposta.status_code == 200
    assert b"filial-sao-luis.jpeg" in resposta.content
    assert b'class="login-visual"' in resposta.content
    assert b">Bem-vindo</h2>" in resposta.content
    assert b"Ambiente corporativo" not in resposta.content
    assert b"Acesso ao sistema" not in resposta.content
    assert b"Controle documental ambiental" not in resposta.content


def test_painel_carrega(client, coordenadora, tipo_licenca):
    client.force_login(coordenadora)
    resposta = client.get(reverse("dashboard:painel"))
    assert resposta.status_code == 200
    assert b'class="mobile-menu-button"' in resposta.content
    assert b'aria-controls="app-sidebar"' in resposta.content
    assert b"NC abertas" not in resposta.content
    destino_envio = reverse(
        "compliance:enviar", args=[coordenadora.unidade.codigo, tipo_licenca.codigo]
    )
    assert f'href="{destino_envio}"'.encode() in resposta.content
    assert b'aria-label="Legenda da matriz de conformidade"' in resposta.content
    assert "Não aplicável" in resposta.content.decode()


def test_matriz_direciona_documento_entregue_para_visualizacao(
    client, coordenadora, casa, tipo_licenca, hoje
):
    from apps.compliance import services

    documento = services.enviar_documento(
        unidade=casa,
        tipo=tipo_licenca,
        identificacao="Documento da matriz",
        data_emissao=hoje,
        usuario=coordenadora,
    )
    client.force_login(coordenadora)
    resposta = client.get(reverse("dashboard:painel"))
    destino = reverse("compliance:detalhe_documento", args=[documento.uuid])
    assert f'href="{destino}"'.encode() in resposta.content


def test_checklist_da_casa(client, coordenadora, casa, tipo_licenca):
    client.force_login(coordenadora)
    resposta = client.get(reverse("dashboard:checklist", args=[casa.codigo]))
    assert resposta.status_code == 200
    assert tipo_licenca.nome.encode() in resposta.content


def test_coordenadora_nao_abre_checklist_de_outra_casa(client, coordenadora, casa_sem_oficina):
    client.force_login(coordenadora)
    resposta = client.get(reverse("dashboard:checklist", args=[casa_sem_oficina.codigo]))
    assert resposta.status_code == 404


def test_upload_por_linha_marca_como_atendido(client, coordenadora, casa, tipo_licenca, hoje):
    from apps.compliance.selectors import checklist_da_unidade

    client.force_login(coordenadora)
    resposta = client.post(
        reverse("compliance:enviar", args=[casa.codigo, tipo_licenca.codigo]),
        {
            "identificacao": "LO 999/2026",
            "numero_protocolo": "PROTO-999",
            "data_emissao": hoje.isoformat(),
            "arquivo": SimpleUploadedFile("lo-999.pdf", b"conteudo", "application/pdf"),
        },
        follow=True,
    )
    assert resposta.status_code == 200
    item = next(i for i in checklist_da_unidade(casa) if i.tipo == tipo_licenca)
    assert item.atendido is True


def test_tipo_com_dois_documentos_exige_e_vincula_anexo_complementar(
    client, coordenadora, casa, tipo_licenca, hoje
):
    from apps.compliance.models import Documento

    tipo_licenca.quantidade_arquivos = 2
    tipo_licenca.nome_anexo_complementar = "Certificado"
    tipo_licenca.save(
        update_fields=["quantidade_arquivos", "nome_anexo_complementar"]
    )
    client.force_login(coordenadora)
    url = reverse("compliance:enviar", args=[casa.codigo, tipo_licenca.codigo])

    pagina = client.get(url)
    assert "Certificado" in pagina.content.decode()

    incompleto = client.post(
        url,
        {
            "identificacao": "MTR sem certificado",
            "data_emissao": hoje.isoformat(),
            "arquivo": SimpleUploadedFile("mtr.pdf", b"mtr", "application/pdf"),
        },
    )
    assert incompleto.status_code == 200
    assert "Este campo é obrigatório" in incompleto.content.decode()

    resposta = client.post(
        url,
        {
            "identificacao": "MTR com certificado",
            "data_emissao": hoje.isoformat(),
            "arquivo": SimpleUploadedFile("mtr.pdf", b"mtr", "application/pdf"),
            "anexo_complementar": SimpleUploadedFile(
                "certificado.pdf", b"certificado", "application/pdf"
            ),
        },
    )
    assert resposta.status_code == 302
    documento = Documento.objects.get(unidade=casa, tipo=tipo_licenca)
    assert Path(documento.arquivo.name).stem.startswith("mtr")
    assert Path(documento.anexo_complementar.name).stem.startswith("certificado")
    assert documento.nome_anexo_complementar == "Certificado"


def test_filtros_da_gestao_documental_usam_componentes_padronizados(
    client, coordenadora
):
    client.force_login(coordenadora)
    resposta = client.get(reverse("compliance:documentos"))
    assert resposta.status_code == 200
    assert resposta.content.count(b'class="inp"') >= 3
    assert b">Limpar</a>" in resposta.content


def test_tela_limita_e_rejeita_data_de_emissao_futura(
    client, coordenadora, casa, tipo_licenca, hoje
):
    client.force_login(coordenadora)
    url = reverse("compliance:enviar", args=[casa.codigo, tipo_licenca.codigo])

    formulario = client.get(url)
    assert f'max="{hoje.isoformat()}"'.encode() in formulario.content

    resposta = client.post(
        url,
        {
            "identificacao": "Documento com emissão futura",
            "data_emissao": (hoje + timedelta(days=1)).isoformat(),
        },
    )
    assert resposta.status_code == 200
    assert "não pode ser posterior" in resposta.content.decode()


def test_upload_sem_data_validade_salva_vencimento_vazio(
    client, coordenadora, casa, tipo_licenca, hoje
):
    from apps.compliance.models import Documento

    client.force_login(coordenadora)
    resposta = client.post(
        reverse("compliance:enviar", args=[casa.codigo, tipo_licenca.codigo]),
        {
            "identificacao": "Documento sem validade",
            "numero_protocolo": "PROTO-SEM-VALIDADE",
            "data_emissao": hoje.isoformat(),
            "sem_data_validade": "on",
            "arquivo": SimpleUploadedFile(
                "sem-validade.pdf", b"conteudo", "application/pdf"
            ),
        },
    )
    assert resposta.status_code == 302
    documento = Documento.objects.get(unidade=casa, tipo=tipo_licenca)
    assert documento.data_vencimento is None
    assert documento.numero_protocolo == "PROTO-SEM-VALIDADE"


def test_envio_exige_apenas_arquivo_e_aceita_protocolo_vazio(
    client, coordenadora, casa, tipo_licenca, hoje
):
    client.force_login(coordenadora)
    resposta = client.post(
        reverse("compliance:enviar", args=[casa.codigo, tipo_licenca.codigo]),
        {"identificacao": "Envio incompleto", "data_emissao": hoje.isoformat()},
    )
    conteudo = resposta.content.decode()
    assert resposta.status_code == 200
    assert conteudo.count("Este campo é obrigatório") == 1

    resposta = client.post(
        reverse("compliance:enviar", args=[casa.codigo, tipo_licenca.codigo]),
        {
            "identificacao": "Documento sem protocolo",
            "data_emissao": hoje.isoformat(),
            "arquivo": SimpleUploadedFile(
                "sem-protocolo.pdf", b"conteudo", "application/pdf"
            ),
        },
    )
    assert resposta.status_code == 302


def test_tela_de_envio_marca_campos_obrigatorios_com_asterisco(
    client, coordenadora, casa, tipo_licenca
):
    client.force_login(coordenadora)
    resposta = client.get(
        reverse("compliance:enviar", args=[casa.codigo, tipo_licenca.codigo])
    )
    conteudo = resposta.content.decode()
    assert "Data de emissao <span class=\"required-mark\">*</span>" in conteudo
    assert "Arquivo (PDF, foto, laudo ou planilha) <span class=\"required-mark\">*</span>" in conteudo
    assert "Numero do protocolo <span class=\"required-mark\">*</span>" not in conteudo


def test_historico_exibe_todas_as_versoes_sem_botoes_de_download(
    client, coordenadora, casa, tipo_licenca, hoje, settings, tmp_path
):
    from apps.compliance import services

    settings.MEDIA_ROOT = tmp_path
    primeira = services.enviar_documento(
        unidade=casa,
        tipo=tipo_licenca,
        identificacao="Licença versão 1",
        data_emissao=hoje,
        usuario=coordenadora,
        arquivo=SimpleUploadedFile("licenca-v1.pdf", b"arquivo-v1", "application/pdf"),
    )
    segunda = services.enviar_documento(
        unidade=casa,
        tipo=tipo_licenca,
        identificacao="Licença versão 2",
        data_emissao=hoje,
        usuario=coordenadora,
        arquivo=SimpleUploadedFile("licenca-v2.pdf", b"arquivo-v2", "application/pdf"),
    )

    client.force_login(coordenadora)
    resposta = client.get(reverse("compliance:detalhe_documento", args=[segunda.uuid]))
    conteudo = resposta.content.decode()
    assert resposta.status_code == 200
    assert "Licença versão 1" in conteudo
    assert "Licença versão 2" in conteudo
    assert reverse("compliance:baixar_documento", args=[primeira.uuid]) not in conteudo
    assert reverse("compliance:baixar_documento", args=[segunda.uuid]) not in conteudo
    assert reverse("compliance:visualizar_documento", args=[primeira.uuid]) in conteudo
    assert reverse("compliance:visualizar_documento", args=[segunda.uuid]) in conteudo

    download = client.get(reverse("compliance:baixar_documento", args=[primeira.uuid]))
    assert download.status_code == 200
    assert b"".join(download.streaming_content) == b"arquivo-v1"
    assert "attachment" in download["Content-Disposition"]

    visualizacao = client.get(
        reverse("compliance:visualizar_documento", args=[primeira.uuid])
    )
    assert visualizacao.status_code == 200
    assert b"".join(visualizacao.streaming_content) == b"arquivo-v1"
    assert "inline" in visualizacao["Content-Disposition"]


def test_aprovacao_exibe_recusa_e_remove_download_superior(
    client, coordenadora, consultoria, casa, tipo_licenca, hoje
):
    from apps.compliance import services

    documento = services.enviar_documento(
        unidade=casa,
        tipo=tipo_licenca,
        identificacao="Documento aguardando aprovação",
        data_emissao=hoje,
        usuario=coordenadora,
    )
    client.force_login(consultoria)
    resposta = client.get(reverse("compliance:detalhe_documento", args=[documento.uuid]))
    conteudo = resposta.content.decode()
    assert resposta.status_code == 200
    assert "Recusar documento" in conteudo
    assert "Motivo da recusa" in conteudo
    assert "Baixar arquivo" not in conteudo


def test_consultoria_valida_cada_versao_individualmente(
    client, coordenadora, consultoria, casa, tipo_licenca, hoje
):
    from apps.compliance import services
    from apps.compliance.enums import SituacaoDocumento

    primeira = services.enviar_documento(
        unidade=casa,
        tipo=tipo_licenca,
        identificacao="Primeira versão aguardando validação",
        data_emissao=hoje,
        usuario=coordenadora,
    )
    segunda = services.enviar_documento(
        unidade=casa,
        tipo=tipo_licenca,
        identificacao="Segunda versão aguardando validação",
        data_emissao=hoje,
        usuario=coordenadora,
    )
    client.force_login(consultoria)

    pagina = client.get(reverse("compliance:detalhe_documento", args=[segunda.uuid]))
    conteudo = pagina.content.decode()
    assert reverse("compliance:validar", args=[primeira.uuid]) in conteudo
    assert reverse("compliance:validar", args=[segunda.uuid]) in conteudo

    resposta = client.post(reverse("compliance:validar", args=[primeira.uuid]))
    assert resposta.status_code == 302
    primeira.refresh_from_db()
    segunda.refresh_from_db()
    assert primeira.situacao == SituacaoDocumento.VALIDADO
    assert segunda.situacao == SituacaoDocumento.AGUARDANDO


def test_consultoria_recusa_cada_versao_individualmente(
    client, coordenadora, consultoria, casa, tipo_licenca, hoje
):
    from apps.compliance import services
    from apps.compliance.enums import SituacaoDocumento

    primeira = services.enviar_documento(
        unidade=casa,
        tipo=tipo_licenca,
        identificacao="Primeira versão para recusa",
        data_emissao=hoje,
        usuario=coordenadora,
    )
    segunda = services.enviar_documento(
        unidade=casa,
        tipo=tipo_licenca,
        identificacao="Segunda versão para recusa",
        data_emissao=hoje,
        usuario=coordenadora,
    )
    client.force_login(consultoria)

    pagina = client.get(reverse("compliance:detalhe_documento", args=[segunda.uuid]))
    conteudo = pagina.content.decode()
    assert reverse("compliance:rejeitar", args=[primeira.uuid]) in conteudo
    assert reverse("compliance:rejeitar", args=[segunda.uuid]) in conteudo

    resposta = client.post(
        reverse("compliance:rejeitar", args=[primeira.uuid]),
        {"motivo": "Arquivo da primeira versão precisa ser corrigido."},
    )
    assert resposta.status_code == 302
    primeira.refresh_from_db()
    segunda.refresh_from_db()
    assert primeira.situacao == SituacaoDocumento.REJEITADO
    assert segunda.situacao == SituacaoDocumento.AGUARDANDO


def test_consultoria_recusa_documento_com_motivo(
    client, coordenadora, consultoria, casa, tipo_licenca, hoje
):
    from apps.compliance import services
    from apps.compliance.enums import SituacaoDocumento

    documento = services.enviar_documento(
        unidade=casa,
        tipo=tipo_licenca,
        identificacao="Documento incorreto",
        data_emissao=hoje,
        usuario=coordenadora,
    )
    client.force_login(consultoria)
    resposta = client.post(
        reverse("compliance:rejeitar", args=[documento.uuid]),
        {"motivo": "Arquivo ilegível; enviar novamente."},
    )
    assert resposta.status_code == 302
    documento.refresh_from_db()
    assert documento.situacao == SituacaoDocumento.REJEITADO
    assert documento.motivo_rejeicao == "Arquivo ilegível; enviar novamente."


def test_download_bloqueia_usuario_sem_acesso_a_unidade(
    client, coordenadora, consultoria, casa_sem_oficina, tipo_licenca, hoje, settings, tmp_path
):
    from apps.compliance import services

    settings.MEDIA_ROOT = tmp_path
    documento = services.enviar_documento(
        unidade=casa_sem_oficina,
        tipo=tipo_licenca,
        identificacao="Documento restrito",
        data_emissao=hoje,
        usuario=consultoria,
        arquivo=SimpleUploadedFile("restrito.pdf", b"restrito", "application/pdf"),
    )
    client.force_login(coordenadora)
    resposta = client.get(reverse("compliance:baixar_documento", args=[documento.uuid]))
    assert resposta.status_code == 404
    visualizacao = client.get(
        reverse("compliance:visualizar_documento", args=[documento.uuid])
    )
    assert visualizacao.status_code == 404


def test_exportacao_csv_do_checklist(client, coordenadora, casa, tipo_licenca):
    client.force_login(coordenadora)
    resposta = client.get(reverse("dashboard:checklist_csv", args=[casa.codigo]))
    assert resposta.status_code == 200
    assert resposta["Content-Type"].startswith("text/csv")


def test_relatorio_de_pendencias_csv(client, consultoria, casa, tipo_licenca):
    client.force_login(consultoria)
    resposta = client.get(reverse("dashboard:pendencias"), {"formato": "csv"})
    assert resposta.status_code == 200
    assert "attachment" in resposta["Content-Disposition"]


def test_relatorio_oferece_acao_ver_para_atualizar_documento(
    client, consultoria, casa, tipo_licenca
):
    client.force_login(consultoria)
    resposta = client.get(reverse("dashboard:pendencias"))
    destino = reverse("compliance:enviar", args=[casa.codigo, tipo_licenca.codigo])
    assert f'href="{destino}">Ver</a>'.encode() in resposta.content


def test_relatorio_de_pendencias_filtra_casa_situacao_e_quem_faz(
    client, consultoria, casa, casa_sem_oficina, tipo_licenca
):
    client.force_login(consultoria)
    resposta = client.get(
        reverse("dashboard:pendencias"),
        {
            "casa": casa.codigo,
            "situacao": "PENDENTE",
            "quem_faz": tipo_licenca.responsavel_execucao,
        },
    )
    assert resposta.status_code == 200
    assert resposta.context["itens"]
    assert all(item.unidade == casa for item in resposta.context["itens"])
    assert all(item.status == "PENDENTE" for item in resposta.context["itens"])
    assert all(
        item.tipo.responsavel_execucao == tipo_licenca.responsavel_execucao
        for item in resposta.context["itens"]
    )


def test_relatorio_filtra_intervalo_de_vencimento_e_preserva_no_csv(
    client, coordenadora, consultoria, casa, tipo_licenca, hoje
):
    from apps.compliance import services

    vencimento = hoje + timedelta(days=5)
    documento = services.enviar_documento(
        unidade=casa,
        tipo=tipo_licenca,
        identificacao="Documento no intervalo",
        data_emissao=hoje,
        data_vencimento=vencimento,
        usuario=coordenadora,
    )
    services.validar_documento(documento=documento, usuario=consultoria)
    client.force_login(consultoria)
    filtros = {
        "data_vencimento_de": vencimento.isoformat(),
        "data_vencimento_ate": vencimento.isoformat(),
    }
    resposta = client.get(reverse("dashboard:pendencias"), filtros)
    assert [item.documento for item in resposta.context["itens"]] == [documento]
    assert "data_vencimento_de" in resposta.context["export_query"]

    resposta_csv = client.get(
        reverse("dashboard:pendencias"), {**filtros, "formato": "csv"}
    )
    assert tipo_licenca.nome.encode() in resposta_csv.content
    assert vencimento.strftime("%d/%m/%Y").encode() in resposta_csv.content


def test_relatorio_filtra_por_cor_da_agenda(
    client, consultoria, casa, tipo_licenca
):
    from apps.compliance.models import CorAgenda

    tipo_licenca.cor_agenda = CorAgenda.AZUL
    tipo_licenca.save(update_fields=["cor_agenda"])
    client.force_login(consultoria)
    resposta = client.get(
        reverse("dashboard:pendencias"), {"cor_agenda": CorAgenda.AZUL}
    )
    assert resposta.status_code == 200
    assert resposta.context["itens"]
    assert all(
        item.tipo.cor_agenda == CorAgenda.AZUL
        for item in resposta.context["itens"]
    )
    assert "cor_agenda=AZUL" in resposta.context["export_query"]
    assert "Cor da agenda" in resposta.content.decode()


def test_api_checklist(client, coordenadora, casa, tipo_licenca):
    client.force_login(coordenadora)
    resposta = client.get(f"/api/documentos/checklist/{casa.codigo}/")
    assert resposta.status_code == 200
    dados = resposta.json()
    assert any(d["tipo"] == tipo_licenca.codigo for d in dados)
