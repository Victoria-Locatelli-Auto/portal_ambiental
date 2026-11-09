"""Funcoes puras de calendario e formatacao usadas no calculo de prazos."""
from __future__ import annotations

import calendar
from datetime import date

from django.utils import timezone


def hoje() -> date:
    """Data corrente no fuso configurado. Ponto unico para facilitar testes."""
    return timezone.localdate()


def somar_meses(base: date, meses: int) -> date:
    """Soma meses preservando o fim do mes (31/01 + 1 mes = 28/02)."""
    if not meses:
        return base
    total = base.month - 1 + meses
    ano = base.year + total // 12
    mes = total % 12 + 1
    dia = min(base.day, calendar.monthrange(ano, mes)[1])
    return date(ano, mes, dia)


def dias_ate(alvo: date | None, referencia: date | None = None) -> int | None:
    """Dias restantes ate `alvo`. Negativo quando ja passou."""
    if alvo is None:
        return None
    return (alvo - (referencia or hoje())).days


def formatar_prazo(dias: int | None) -> str:
    if dias is None:
        return "sem prazo"
    if dias < 0:
        return f"venceu ha {abs(dias)} dias"
    if dias == 0:
        return "vence hoje"
    return f"{dias} dias"
