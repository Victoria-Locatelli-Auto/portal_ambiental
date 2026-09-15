"""Filtros de apresentacao do SIGA."""
from __future__ import annotations

from django import template

from apps.compliance.enums import StatusConformidade

register = template.Library()

_CLASSES = {
    StatusConformidade.VIGENTE: "p-ok",
    StatusConformidade.AVENCER: "p-warn",
    StatusConformidade.CRITICO: "p-crit",
    StatusConformidade.VENCIDO: "p-venc",
    StatusConformidade.EM_ANALISE: "p-info",
    StatusConformidade.PENDENTE: "p-pend",
    StatusConformidade.NAO_APLICAVEL: "p-na",
}
_SIMBOLOS = {
    StatusConformidade.VIGENTE: "OK",
    StatusConformidade.AVENCER: "!",
    StatusConformidade.CRITICO: "!",
    StatusConformidade.VENCIDO: "X",
    StatusConformidade.EM_ANALISE: "~",
    StatusConformidade.PENDENTE: ".",
    StatusConformidade.NAO_APLICAVEL: "-",
}


@register.filter
def classe_status(status: str) -> str:
    return _CLASSES.get(status, "p-pend")


@register.filter
def simbolo_status(status: str) -> str:
    return _SIMBOLOS.get(status, ".")


@register.filter
def rotulo_status(status: str) -> str:
    return StatusConformidade(status).label if status else ""


@register.filter
def cor_percentual(valor: int) -> str:
    if valor >= 90:
        return "#157347"
    if valor >= 70:
        return "#d3a115"
    if valor >= 50:
        return "#e2680f"
    return "#b02a37"


@register.filter
def linha_matriz(matriz: dict, chave) -> dict:
    return matriz.get(chave, {})


@register.filter
def item(dicionario: dict, chave):
    return dicionario.get(chave) if dicionario else None
