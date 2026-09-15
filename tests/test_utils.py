"""Calendario e calculo de prazos."""
from datetime import date

import pytest

from apps.core.utils import dias_ate, formatar_prazo, somar_meses


@pytest.mark.parametrize(
    ("base", "meses", "esperado"),
    [
        (date(2026, 1, 31), 1, date(2026, 2, 28)),   # fim de mes curto
        (date(2024, 1, 31), 1, date(2024, 2, 29)),   # ano bissexto
        (date(2026, 5, 22), 48, date(2030, 5, 22)),  # licenca de 4 anos
        (date(2026, 12, 15), 3, date(2027, 3, 15)),  # virada de ano
        (date(2026, 6, 10), 0, date(2026, 6, 10)),   # por evento
    ],
)
def test_somar_meses(base, meses, esperado):
    assert somar_meses(base, meses) == esperado


def test_dias_ate_negativo_quando_passado():
    assert dias_ate(date(2026, 1, 1), referencia=date(2026, 1, 11)) == -10


def test_dias_ate_none():
    assert dias_ate(None) is None


def test_formatar_prazo():
    assert formatar_prazo(-5) == "venceu ha 5 dias"
    assert formatar_prazo(0) == "vence hoje"
    assert formatar_prazo(30) == "30 dias"
