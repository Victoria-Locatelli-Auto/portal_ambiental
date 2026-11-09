from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.accounts.models import Perfil
from apps.compliance import services as compliance_services
from apps.compliance.forms import EnvioDocumentoForm
from apps.fornecedores.models import Contrato, Fornecedor

Usuario = get_user_model()


@pytest.fixture
def administrador_fornecedores(db):
    return Usuario.objects.create_user(
        username="admin-fornecedores",
        email="admin-fornecedores@mcm.com.br",
        password="senha-segura",
        nome_completo="Administrador de Fornecedores",
        perfil=Perfil.ADMIN,
    )


@pytest.fixture
def fornecedor(db):
    return Fornecedor.objects.create(
        razao_social="Ambiental Serviços Ltda",
        nome_fantasia="Ambiental Serviços",
        cnpj_cpf="12.345.678/0001-90",
        servico_fornecido="Coleta de resíduos",
    )


def test_somente_administrador_acessa_fornecedores(client, coordenadora):
    client.force_login(coordenadora)
    assert client.get(reverse("fornecedores:lista")).status_code == 403


def test_administrador_cadastra_fornecedor(client, administrador_fornecedores):
    client.force_login(administrador_fornecedores)
    resposta = client.post(
        reverse("fornecedores:criar"),
        {
            "razao_social": "Fornecedor Teste Ltda",
            "nome_fantasia": "Fornecedor Teste",
            "cnpj_cpf": "11.222.333/0001-44",
            "servico_fornecido": "Consultoria ambiental",
            "responsavel": "Maria Silva",
            "email": "maria@fornecedor.com.br",
            "telefone": "(63) 99999-0000",
            "endereco": "Palmas - TO",
            "observacoes": "Fornecedor homologado.",
            "ativo": "on",
        },
    )
    assert resposta.status_code == 302
    assert Fornecedor.objects.filter(cnpj_cpf="11.222.333/0001-44", ativo=True).exists()


def test_formulario_fornecedor_exibe_anexo_de_contrato(
    client, administrador_fornecedores
):
    client.force_login(administrador_fornecedores)
    resposta = client.get(reverse("fornecedores:criar"))
    conteudo = resposta.content.decode()
    assert "Anexo do contrato" in conteudo
    assert 'name="anexo_contrato"' in conteudo
    assert 'enctype="multipart/form-data"' in conteudo


def test_formulario_fornecedor_exibe_cidades_em_seletor_de_checkboxes(
    client, administrador_fornecedores, casa, casa_sem_oficina
):
    client.force_login(administrador_fornecedores)
    resposta = client.get(reverse("fornecedores:criar"))
    conteudo = resposta.content.decode()
    assert "Cidades atendidas" in conteudo
    assert casa.municipio in conteudo
    assert casa_sem_oficina.municipio in conteudo
    assert 'class="checkbox-dropdown"' in conteudo
    assert 'type="checkbox"' in conteudo


def test_administrador_cadastra_contrato(
    client, administrador_fornecedores, fornecedor, settings, tmp_path
):
    settings.MEDIA_ROOT = tmp_path
    client.force_login(administrador_fornecedores)
    resposta = client.post(
        reverse("fornecedores:contrato_criar", args=[fornecedor.uuid]),
        {
            "numero": "CT-2026-001",
            "objeto": "Coleta e destinação de resíduos.",
            "data_inicio": "2026-01-01",
            "data_fim": "2026-12-31",
            "valor": "12500.00",
            "situacao": "VIGENTE",
            "arquivo": SimpleUploadedFile(
                "contrato.pdf", b"%PDF-1.4 contrato de teste", content_type="application/pdf"
            ),
            "observacoes": "Renovação anual.",
        },
    )
    assert resposta.status_code == 302
    contrato = Contrato.objects.get(fornecedor=fornecedor, numero="CT-2026-001")
    assert contrato.data_fim == date(2026, 12, 31)
    assert contrato.arquivo.name.endswith("contrato.pdf")


def test_contrato_rejeita_fim_anterior_ao_inicio(
    client, administrador_fornecedores, fornecedor
):
    client.force_login(administrador_fornecedores)
    resposta = client.post(
        reverse("fornecedores:contrato_criar", args=[fornecedor.uuid]),
        {
            "numero": "CT-INVALIDO",
            "objeto": "Contrato inválido.",
            "data_inicio": "2026-12-31",
            "data_fim": "2026-01-01",
            "situacao": "VIGENTE",
        },
    )
    assert resposta.status_code == 200
    assert "fim da vigência não pode ser anterior" in resposta.content.decode()
    assert not Contrato.objects.filter(numero="CT-INVALIDO").exists()


def test_menu_de_fornecedores_aparece_para_administrador(
    client, administrador_fornecedores
):
    client.force_login(administrador_fornecedores)
    resposta = client.get(reverse("fornecedores:lista"))
    assert resposta.status_code == 200
    assert "Fornecedores" in resposta.content.decode()


def test_envio_documento_lista_somente_fornecedores_ativos(fornecedor):
    inativo = Fornecedor.objects.create(
        razao_social="Fornecedor Inativo Ltda",
        cnpj_cpf="99.999.999/0001-99",
        servico_fornecido="Serviço encerrado",
        ativo=False,
    )
    formulario = EnvioDocumentoForm()
    fornecedores = formulario.fields["fornecedor"].queryset
    assert fornecedor in fornecedores
    assert inativo not in fornecedores


def test_documento_enviado_fica_vinculado_ao_fornecedor(
    fornecedor, coordenadora, casa, tipo_licenca, hoje
):
    documento = compliance_services.enviar_documento(
        unidade=casa,
        tipo=tipo_licenca,
        identificacao="Documento do fornecedor",
        data_emissao=hoje,
        usuario=coordenadora,
        fornecedor=fornecedor,
    )
    assert documento.fornecedor == fornecedor


def test_formulario_contrato_exibe_campo_de_anexo(
    client, administrador_fornecedores, fornecedor
):
    client.force_login(administrador_fornecedores)
    resposta = client.get(
        reverse("fornecedores:contrato_criar", args=[fornecedor.uuid])
    )
    conteudo = resposta.content.decode()
    assert "Anexo do contrato" in conteudo
    assert 'type="file"' in conteudo

