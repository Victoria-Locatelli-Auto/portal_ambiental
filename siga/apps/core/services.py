"""Servicos transversais."""
from __future__ import annotations

from typing import Any

from apps.core.middleware import get_usuario_atual
from apps.core.models import LogAuditoria


def registrar(
    acao: str,
    objeto: str,
    *,
    detalhe: str = "",
    usuario: Any = None,
    entidade: str = "",
    entidade_id: str | int = "",
) -> LogAuditoria:
    """Grava um evento na trilha de auditoria.

    O usuario e resolvido do contexto da requisicao quando nao informado, o que
    permite chamar este servico de dentro de sinais sem acoplar a view.
    """
    usuario = usuario or get_usuario_atual()
    nome = getattr(usuario, "nome_exibicao", None) or (str(usuario) if usuario else "Sistema")
    return LogAuditoria.objects.create(
        usuario=usuario if getattr(usuario, "pk", None) else None,
        usuario_nome=nome,
        acao=acao,
        objeto=objeto[:255],
        detalhe=detalhe,
        entidade=entidade,
        entidade_id=str(entidade_id),
    )
