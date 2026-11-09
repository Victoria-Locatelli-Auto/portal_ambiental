"""Disponibiliza o usuario da requisicao para a camada de servicos."""
from __future__ import annotations

import contextvars
from collections.abc import Callable
from typing import Any

from django.http import HttpRequest, HttpResponse

_usuario_atual: contextvars.ContextVar[Any] = contextvars.ContextVar("usuario_atual", default=None)


def get_usuario_atual() -> Any:
    return _usuario_atual.get()


class UsuarioAtualMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        usuario = getattr(request, "user", None)
        token = _usuario_atual.set(usuario if getattr(usuario, "is_authenticated", False) else None)
        try:
            return self.get_response(request)
        finally:
            _usuario_atual.reset(token)
