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
from apps.compliance.models import CorAgenda, TipoDocumento

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
            "responsavel_execucao": ResponsavelExecucao.CASA,
            "base_legal": "Base legal de teste",
            "instrucao": "Providenciar o documento.",
            "nota_tecnica": "",
            "ativo": "on",
        },
    )
    assert resposta.status_code == 302
    tipo = TipoDocumento.objects.get(codigo="TX9", ativo=True)
    assert tipo.cor_agenda == CorAgenda.MARROM


def test_formulario_tipo_exibe_cores_da_agenda(client, administrador):
    client.force_login(administrador)
    resposta = client.get(reverse("administracao:tipo_criar"))
    assert resposta.status_code == 200
    assert b"Cor da agenda" in resposta.content
    assert b'value="VERDE"' in resposta.content
    assert b'value="MARROM"' in resposta.content
    assert b'value="AZUL"' in resposta.content


def test_formulario_tipo_exibe_tema_condicionantes_sem_campo_de_regras(client, administrador):
    client.force_login(administrador)
    resposta = client.get(reverse("administracao:tipo_criar"))
    assert resposta.status_code == 200
    assert b'value="CONDICIONANTES"' in resposta.content
    assert "Regras a serem seguidas" not in resposta.content.decode()


def test_formulario_tipo_exibe_unidades_em_aplicabilidade_e_execucao(
    client, administrador, casa, casa_sem_oficina
):
    client.force_login(administrador)
    resposta = client.get(reverse("administracao:tipo_criar"))
    conteudo = resposta.content.decode()
    for nome in (casa.nome, casa_sem_oficina.nome):
        assert conteudo.count(nome) == 2
    assert "Gurupi" not in conteudo


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
