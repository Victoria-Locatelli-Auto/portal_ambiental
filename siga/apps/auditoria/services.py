"""Regras de escrita de nao conformidades."""
from __future__ import annotations

from datetime import date

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from apps.auditoria.models import NaoConformidade
from apps.core.models import LogAuditoria
from apps.core.services import registrar


def proximo_codigo(ano: int | None = None) -> str:
    """Gera NC-<ano>-<sequencial> de forma previsivel."""
    ano = ano or timezone.localdate().year
    prefixo = f"NC-{ano}-"
    ultimo = (
        NaoConformidade.objects.filter(codigo__startswith=prefixo).order_by("-codigo").first()
    )
    sequencial = int(ultimo.codigo.rsplit("-", 1)[1]) + 1 if ultimo else 1
    return f"{prefixo}{sequencial:03d}"


@transaction.atomic
def abrir_nao_conformidade(*, usuario=None, **dados) -> NaoConformidade:
    dados.setdefault("codigo", proximo_codigo())
    dados.setdefault("data_abertura", timezone.localdate())
    nc = NaoConformidade.objects.create(**dados)
    registrar(
        LogAuditoria.Acao.CRIACAO,
        f"{nc.codigo} - {nc.unidade.nome}",
        detalhe=nc.descricao[:200],
        usuario=usuario,
        entidade="NaoConformidade",
        entidade_id=nc.pk,
    )
    return nc


@transaction.atomic
def encerrar_nao_conformidade(
    *, nc: NaoConformidade, usuario, evidencia: str, data: date | None = None
) -> NaoConformidade:
    if usuario.somente_leitura:
        raise PermissionDenied("Perfil somente leitura nao encerra nao conformidades.")
    nc.situacao = NaoConformidade.Situacao.ENCERRADA
    nc.encerrada_em = data or timezone.localdate()
    nc.evidencia_encerramento = evidencia
    nc.save(update_fields=["situacao", "encerrada_em", "evidencia_encerramento"])
    registrar(
        LogAuditoria.Acao.ALTERACAO,
        f"Encerrou {nc.codigo}",
        detalhe=evidencia[:200],
        usuario=usuario,
        entidade="NaoConformidade",
        entidade_id=nc.pk,
    )
    return nc
