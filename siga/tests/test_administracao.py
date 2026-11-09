"""Permissões e fluxos essenciais da administração integrada."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import Perfil
from apps.compliance.enums import (
    Aplicabilidade,
    ResponsavelExecucao,
    TemaLegal,
    valor_unidade,
)
from apps.compliance.models import CorAgenda, TemaLegalCadastro, TipoDocumento
from apps.organizacao.models import Unidade

Usuario = get_user_model()


@pytest.fixture
def administrador(db):
    return Usuario.objects.create_user(
        username="admin-teste",
        email="admin-teste@mcm.com.br",
        password="senha-segura",
        nome_completo="Administrador Teste",
        perfil=Perfil.ADMIN,
    )


def test_apenas_administrador_acessa_configuracao(client, coordenadora):
    client.force_login(coordenadora)
    resposta = client.get(reverse("administracao:inicio"))
    assert resposta.status_code == 403


def test_administrador_visualiza_submenus(client, administrador):
    client.force_login(administrador)
    resposta = client.get(reverse("administracao:inicio"))
    assert resposta.status_code == 200
    assert b"Tipos documentais" in resposta.content
    assert b"Acessos e usu" in resposta.content


def test_administrador_cria_tipo_documental(client, administrador):
    client.force_login(administrador)
    resposta = client.post(
        reverse("administracao:tipo_criar"),
        {
            "codigo": "TX9",
            "nome": "Documento criado na configuração",
            "tema": TemaLegal.LICENCIAMENTO,
            "cor_agenda": CorAgenda.MARROM,
            "ordem": 99,
            "periodicidade_meses": 12,
            "dias_alerta": 60,
            "aplicabilidade": Aplicabilidade.TODAS,
            "responsavel_execucao": ResponsavelExecucao.MCM,
            "base_legal": "Base legal de teste",
            "instrucao": "Providenciar o documento.",
            "nota_tecnica": "",
            "ativo": "on",
        },
    )
    assert resposta.status_code == 302
    tipo = TipoDocumento.objects.get(codigo="TX9", ativo=True)
    assert tipo.cor_agenda == CorAgenda.MARROM


def test_administrador_cadastra_tema_legal(client, administrador):
    client.force_login(administrador)
    resposta = client.post(
        reverse("administracao:tema_criar"),
        {"codigo": "FAUNA", "nome": "Fauna", "ordem": 150, "ativo": "on"},
    )
    assert resposta.status_code == 302
    assert TemaLegalCadastro.objects.filter(codigo="FAUNA", ativo=True).exists()

    formulario = client.get(reverse("administracao:tipo_criar")).context["formulario"]
    assert ("FAUNA", "Fauna") in list(formulario.fields["tema"].choices)


def test_apenas_administrador_acessa_temas_legais(client, coordenadora):
    client.force_login(coordenadora)
    assert client.get(reverse("administracao:temas")).status_code == 403


def test_formulario_tipo_exibe_cores_da_agenda(client, administrador):
    client.force_login(administrador)
    resposta = client.get(reverse("administracao:tipo_criar"))
    assert resposta.status_code == 200
    assert b"Cor da agenda" in resposta.content
    assert b'value="VERDE"' in resposta.content
    assert b'value="MARROM"' in resposta.content
    assert b'value="AZUL"' in resposta.content


def test_formulario_tipo_exibe_rotulo_validade_do_documento(client, administrador):
    client.force_login(administrador)
    resposta = client.get(reverse("administracao:tipo_criar"))
    conteudo = resposta.content.decode()
    assert "Validade do documento" in conteudo
    assert "Validade em meses" not in conteudo


def test_formulario_tipo_nao_exibe_ordem_de_exibicao(client, administrador):
    client.force_login(administrador)
    resposta = client.get(reverse("administracao:tipo_criar"))
    assert "Ordem de exibicao" not in resposta.content.decode()


def test_formulario_tipo_exibe_tema_condicionantes_sem_campo_de_regras(client, administrador):
    client.force_login(administrador)
    resposta = client.get(reverse("administracao:tipo_criar"))
    assert resposta.status_code == 200
    assert b'value="CONDICIONANTES"' in resposta.content
    assert "Regras a serem seguidas" not in resposta.content.decode()


def test_formulario_tipo_exibe_rotulos_revisados(client, administrador):
    client.force_login(administrador)
    resposta = client.get(reverse("administracao:tipo_criar"))
    formulario = resposta.context["formulario"]
    temas = dict(formulario.fields["tema"].choices)

    assert formulario.fields["codigo"].label == "Código"
    assert formulario.fields["dias_alerta"].label == "Antecedência do alerta"
    assert formulario.fields["dias_alerta"].help_text == ""
    assert formulario.fields["nota_tecnica"].label == "Observação técnica"
    assert temas[TemaLegal.HIDRICOS] == "Recursos hídricos"
    assert temas[TemaLegal.RESIDUOS] == "Resíduos"
    assert temas[TemaLegal.SOLO] == "Solo e a água subterrânea"
    assert temas[TemaLegal.POSTO] == "Posto de combustível"
    assert temas[TemaLegal.SGA] == "Gestão/SGA"
    assert temas[TemaLegal.EMERGENCIA] == "Emergência"
    assert temas[TemaLegal.SEGURANCA] == "Segurança"
    assert temas[TemaLegal.SST] == "Saúde e segurança do trabalho"


def test_tipo_documental_configura_um_ou_dois_documentos(client, administrador):
    client.force_login(administrador)
    resposta = client.get(reverse("administracao:tipo_criar"))
    formulario = resposta.context["formulario"]

    assert list(formulario.fields["quantidade_arquivos"].choices) == [
        (1, "1 documento"),
        (2, "2 documentos relacionados"),
    ]
    assert formulario.fields["quantidade_arquivos"].initial == 1


def test_tipo_com_dois_documentos_exige_nome_do_segundo(client, administrador):
    client.force_login(administrador)
    resposta = client.post(
        reverse("administracao:tipo_criar"),
        {
            "codigo": "MTR1",
            "nome": "MTR",
            "tema": TemaLegal.RESIDUOS,
            "cor_agenda": CorAgenda.VERDE,
            "periodicidade_meses": 12,
            "dias_alerta": 60,
            "quantidade_arquivos": 2,
            "nome_anexo_complementar": "",
            "aplicabilidade": [Aplicabilidade.TODAS],
            "responsavel_execucao": [ResponsavelExecucao.MCM],
            "base_legal": "Base legal",
            "instrucao": "Enviar MTR e certificado.",
            "nota_tecnica": "",
            "ativo": "on",
        },
    )

    assert resposta.status_code == 200
    assert "Informe o nome do segundo documento." in resposta.content.decode()


def test_formulario_tipo_exibe_unidades_em_aplicabilidade_e_execucao(
    client, administrador, casa, casa_sem_oficina
):
    client.force_login(administrador)
    resposta = client.get(reverse("administracao:tipo_criar"))
    conteudo = resposta.content.decode()
    for nome in (casa.nome, casa_sem_oficina.nome):
        assert conteudo.count(nome) == 2
    assert "Gurupi" not in conteudo


def test_aplicabilidade_exibe_somente_todas_e_casas(
    client, administrador, casa, casa_sem_oficina
):
    client.force_login(administrador)
    resposta = client.get(reverse("administracao:tipo_criar"))
    conteudo = resposta.content.decode()
    assert "Todas as casas" in conteudo
    assert "Somente casas com oficina" not in conteudo
    assert "Somente casas com captacao propria" not in conteudo
    assert "Somente casa em area de posto" not in conteudo
    assert "Somente casas em imovel de terceiro" not in conteudo


def test_aprovador_exibe_somente_opcoes_permitidas(
    client, administrador, casa, casa_sem_oficina
):
    Unidade.objects.create(
        codigo="U7",
        nome="Sao Luis - Posto Roma (Vila Maranhao)",
        uf="MA",
        municipio="Sao Luis",
        cnpj="00.000.000/0007-00",
    )
    Unidade.objects.create(
        codigo="U10",
        nome="Palmas",
        uf="TO",
        municipio="Palmas",
        cnpj="00.000.000/0008-00",
    )
    client.force_login(administrador)
    resposta = client.get(reverse("administracao:tipo_criar"))
    escolhas = dict(resposta.context["formulario"].fields["responsavel_execucao"].choices)

    assert list(escolhas) == [
        ResponsavelExecucao.MCM,
        ResponsavelExecucao.STX,
        valor_unidade(casa_sem_oficina.codigo),
        valor_unidade(casa.codigo),
        valor_unidade("U10"),
    ]
    assert ResponsavelExecucao.CASA not in escolhas
    assert ResponsavelExecucao.MCM_STX not in escolhas
    assert ResponsavelExecucao.STX_ELABORA not in escolhas
    assert valor_unidade("U7") not in escolhas


def test_todas_as_casas_salva_todas_as_unidades(
    client, administrador, casa, casa_sem_oficina
):
    client.force_login(administrador)
    resposta = client.post(
        reverse("administracao:tipo_criar"),
        {
            "codigo": "TM2",
            "nome": "Documento para todas as casas",
            "tema": TemaLegal.LICENCIAMENTO,
            "cor_agenda": CorAgenda.VERDE,
            "ordem": 101,
            "periodicidade_meses": 12,
            "dias_alerta": 60,
            "aplicabilidade": [Aplicabilidade.TODAS],
            "responsavel_execucao": [ResponsavelExecucao.MCM],
            "base_legal": "Base legal",
            "instrucao": "Providenciar o documento.",
            "nota_tecnica": "",
            "ativo": "on",
        },
    )
    assert resposta.status_code == 302
    tipo = TipoDocumento.objects.get(codigo="TM2")
    assert tipo.aplicabilidades[0] == Aplicabilidade.TODAS
    assert set(tipo.aplicabilidades[1:]) == {
        valor_unidade(casa.codigo),
        valor_unidade(casa_sem_oficina.codigo),
    }


def test_posto_roma_nao_aparece_nem_e_incluido_em_todas_as_casas(
    client, administrador, casa
):
    posto_roma = Unidade.objects.create(
        codigo="U7",
        nome="Sao Luis - Posto Roma (Vila Maranhao)",
        uf="MA",
        municipio="Sao Luis",
        cnpj="00.000.000/0007-00",
    )
    client.force_login(administrador)
    resposta = client.get(reverse("administracao:tipo_criar"))
    escolhas = dict(resposta.context["formulario"].fields["aplicabilidade"].choices)
    assert valor_unidade(posto_roma.codigo) not in escolhas

    resposta = client.post(
        reverse("administracao:tipo_criar"),
        {
            "codigo": "TM3",
            "nome": "Documento sem Posto Roma",
            "tema": TemaLegal.LICENCIAMENTO,
            "cor_agenda": CorAgenda.VERDE,
            "ordem": 102,
            "periodicidade_meses": 12,
            "dias_alerta": 60,
            "aplicabilidade": [Aplicabilidade.TODAS],
            "responsavel_execucao": [ResponsavelExecucao.MCM],
            "base_legal": "Base legal",
            "instrucao": "Providenciar o documento.",
            "nota_tecnica": "",
            "ativo": "on",
        },
    )
    assert resposta.status_code == 302
    tipo = TipoDocumento.objects.get(codigo="TM3")
    assert valor_unidade(casa.codigo) in tipo.aplicabilidades
    assert valor_unidade(posto_roma.codigo) not in tipo.aplicabilidades


def test_administrador_salva_multiplas_aplicabilidades_e_executores(
    client, administrador, casa, casa_sem_oficina
):
    client.force_login(administrador)
    resposta = client.post(
        reverse("administracao:tipo_criar"),
        {
            "codigo": "TM1",
            "nome": "Documento com múltiplos responsáveis",
            "tema": TemaLegal.CONDICIONANTES,
            "cor_agenda": CorAgenda.VERDE,
            "ordem": 100,
            "periodicidade_meses": 0,
            "dias_alerta": 60,
            "aplicabilidade": [
                valor_unidade(casa.codigo),
                valor_unidade(casa_sem_oficina.codigo),
            ],
            "responsavel_execucao": [ResponsavelExecucao.MCM, ResponsavelExecucao.STX],
            "base_legal": "Licença ambiental",
            "instrucao": "Atender às condicionantes.",
            "nota_tecnica": "",
            "ativo": "on",
        },
    )
    assert resposta.status_code == 302
    tipo = TipoDocumento.objects.get(codigo="TM1")
    assert tipo.aplicabilidades == [
        valor_unidade(casa.codigo),
        valor_unidade(casa_sem_oficina.codigo),
    ]
    assert tipo.responsaveis_execucao == [ResponsavelExecucao.MCM, ResponsavelExecucao.STX]
    assert tipo.get_responsavel_execucao_display() == "MCM (matriz), STX Engenharia"


def test_desativacao_preserva_tipo_documental(client, administrador, tipo_licenca):
    client.force_login(administrador)
    resposta = client.post(reverse("administracao:tipo_alternar", args=[tipo_licenca.uuid]))
    assert resposta.status_code == 302
    tipo_licenca.refresh_from_db()
    assert not tipo_licenca.ativo


def test_administrador_cria_usuario_com_senha(client, administrador, casa):
    client.force_login(administrador)
    resposta = client.post(
        reverse("administracao:usuario_criar"),
        {
            "nome_completo": "Nova Responsável",
            "email": "nova.responsavel@mcm.com.br",
            "cargo": "Coordenadora",
            "telefone": "",
            "perfil": Perfil.UNIDADE,
            "unidade": casa.pk,
            "recebe_notificacoes": "on",
            "is_active": "on",
            "senha": "senha-inicial-123",
            "confirmar_senha": "senha-inicial-123",
        },
    )
    assert resposta.status_code == 302
    usuario = Usuario.objects.get(email="nova.responsavel@mcm.com.br")
    assert usuario.check_password("senha-inicial-123")
    assert usuario.unidade == casa
