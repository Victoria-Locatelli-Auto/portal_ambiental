"""Executa a regua de notificacoes pela linha de comando.

Uso:
    python manage.py enviar_notificacoes --previa
    python manage.py enviar_notificacoes --alertas --cobrancas
"""
from __future__ import annotations

from datetime import datetime

from django.core.management.base import BaseCommand

from apps.notificacoes import services


class Command(BaseCommand):
    help = "Processa a regua de notificacoes de vencimento e as cobrancas de checklist."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--previa", action="store_true", help="Simula sem enviar nem gravar.")
        parser.add_argument("--alertas", action="store_true", help="Somente alertas e vencidos.")
        parser.add_argument("--cobrancas", action="store_true", help="Somente cobranca semanal.")
        parser.add_argument("--data", help="Data de referencia AAAA-MM-DD (padrao: hoje).")

    def handle(self, *args, **opcoes) -> None:
        referencia = (
            datetime.strptime(opcoes["data"], "%Y-%m-%d").date() if opcoes.get("data") else None
        )
        so_alertas = opcoes["alertas"]
        so_cobrancas = opcoes["cobrancas"]
        tudo = not (so_alertas or so_cobrancas)

        if opcoes["previa"]:
            mensagens = services.previa(referencia)
            self.stdout.write(self.style.WARNING(f"PREVIA - {len(mensagens)} mensagem(ns):\n"))
            for m in mensagens:
                self.stdout.write(f"  [{m.tipo:9}] {m.destinatario:34} {m.assunto}")
            return

        total = 0
        if tudo or so_alertas:
            enviadas = services.processar_alertas(referencia)
            total += len(enviadas)
            self.stdout.write(self.style.SUCCESS(f"Alertas/vencidos: {len(enviadas)}"))
        if tudo or so_cobrancas:
            enviadas = services.processar_cobrancas(referencia)
            total += len(enviadas)
            self.stdout.write(self.style.SUCCESS(f"Cobrancas de checklist: {len(enviadas)}"))
        self.stdout.write(self.style.SUCCESS(f"Total enviado: {total}"))
