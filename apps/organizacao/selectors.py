"""Consultas de leitura sobre casas. Sem efeito colateral."""
from __future__ import annotations

from apps.organizacao.models import Unidade


def unidades_do_usuario(usuario) -> "models.QuerySet[Unidade]":  # noqa: F821
    """Aplica o escopo do perfil. Ponto unico de filtragem por permissao."""
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        return Unidade.objects.none()
    return usuario.unidades_visiveis()


def unidade_por_codigo(codigo: str) -> Unidade:
    return Unidade.objects.ativos().get(codigo=codigo)
