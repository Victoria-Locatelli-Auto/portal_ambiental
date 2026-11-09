"""Carga inicial do SIGA.

Popula o catalogo legal, as 7 casas da MCM, os usuarios de cada perfil e o
acervo levantado nos Relatorios de Auditoria 001 da STX Engenharia
(visitas de 25 a 27/06/2025).

Uso:
    python manage.py seed_siga            # idempotente, pode rodar de novo
    python manage.py seed_siga --limpar   # apaga e recarrega
"""
from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.auditoria.models import (
    NaoConformidade,
    PontoVerificacao,
    RelatorioAuditoria,
    RespostaCampo,
)
from apps.compliance.enums import (
    Aplicabilidade,
    ResponsavelExecucao,
    SituacaoDocumento,
    TemaLegal,
)
from apps.compliance.models import Condicionante, Documento, NormaLegal, TipoDocumento
from apps.core.fixtures import dados
from apps.organizacao.models import Unidade
from apps.residuos.models import MovimentacaoResiduo

Usuario = get_user_model()


class Command(BaseCommand):
    help = "Carrega catalogo legal, casas, usuarios e o acervo das auditorias STX."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--limpar", action="store_true", help="Apaga os dados antes de carregar.")
        parser.add_argument("--senha", default="siga2026", help="Senha dos usuarios de demonstracao.")

    @transaction.atomic
    def handle(self, *args, **opcoes) -> None:
        if opcoes["limpar"]:
            self.stdout.write(self.style.WARNING("Limpando dados..."))
            for modelo in (
                RespostaCampo, NaoConformidade, RelatorioAuditoria, MovimentacaoResiduo,
                Condicionante, Documento, TipoDocumento, NormaLegal, PontoVerificacao,
            ):
                modelo.objects.all().delete()
            Usuario.objects.filter(is_superuser=False).delete()
            Unidade.objects.all().delete()

        self._normas()
        self._tipos()
        casas = self._casas()
        self._usuarios(casas, opcoes["senha"])
        relatorios = self._relatorios(casas)
        self._checklist_campo(relatorios)
        self._documentos(casas)
        self._condicionantes(casas)
        self._nao_conformidades(casas, relatorios)
        self._residuos(casas)

        self.stdout.write(self.style.SUCCESS("\n=== SIGA carregado ==="))
        self.stdout.write(f"  Casas ..................: {Unidade.objects.count()}")
        self.stdout.write(f"  Requisitos legais ......: {TipoDocumento.objects.count()}")
        self.stdout.write(f"  Normas .................: {NormaLegal.objects.count()}")
        self.stdout.write(f"  Usuarios ...............: {Usuario.objects.count()}")
        self.stdout.write(f"  Documentos .............: {Documento.objects.count()}")
        self.stdout.write(f"  Nao conformidades ......: {NaoConformidade.objects.count()}")
        self.stdout.write(f"  Pontos de checklist ....: {PontoVerificacao.objects.count()}")
        self.stdout.write(f"  Movimentacoes de residuo: {MovimentacaoResiduo.objects.count()}")
        self.stdout.write(
            self.style.SUCCESS(f"\nLogin de demonstracao - senha: {opcoes['senha']}")
        )
        for u in Usuario.objects.order_by("perfil"):
            self.stdout.write(f"  {u.email:34} {u.get_perfil_display()}")

    # ------------------------------------------------------------------ blocos
    def _normas(self) -> None:
        for identificacao, objeto, esfera in dados.NORMAS:
            NormaLegal.objects.update_or_create(
                identificacao=identificacao, defaults={"objeto": objeto, "esfera": esfera}
            )

    def _tipos(self) -> None:
        for ordem, t in enumerate(dados.TIPOS_DOCUMENTO, start=1):
            TipoDocumento.objects.update_or_create(
                codigo=t["codigo"],
                defaults={
                    "nome": t["nome"],
                    "tema": t["tema"],
                    "periodicidade_meses": t["periodicidade"],
                    "dias_alerta": t["alerta"],
                    "aplicabilidade": t["aplicabilidade"],
                    "responsavel_execucao": t["responsavel"],
                    "base_legal": t["base_legal"],
                    "instrucao": t["instrucao"],
                    "nota_tecnica": t.get("nota", ""),
                    "ordem": ordem,
                },
            )

    def _casas(self) -> dict[str, Unidade]:
        casas: dict[str, Unidade] = {}
        for c in dados.CASAS:
            casas[c["codigo"]], _ = Unidade.objects.update_or_create(
                codigo=c["codigo"], defaults={k: v for k, v in c.items() if k != "codigo"}
            )
        return casas

    def _usuarios(self, casas: dict[str, Unidade], senha: str) -> None:
        for u in dados.USUARIOS:
            usuario, criado = Usuario.objects.update_or_create(
                email=u["email"],
                defaults={
                    "username": u["email"].split("@")[0],
                    "nome_completo": u["nome"],
                    "cargo": u.get("cargo", ""),
                    "perfil": u["perfil"],
                    "unidade": casas.get(u.get("casa")),
                    "is_staff": u["perfil"] in {"ADMIN", "GESTOR"},
                    "is_superuser": u["perfil"] == "ADMIN",
                },
            )
            if criado or not usuario.has_usable_password():
                usuario.set_password(senha)
                usuario.save(update_fields=["password"])

    def _relatorios(self, casas: dict[str, Unidade]) -> dict[str, RelatorioAuditoria]:
        relatorios: dict[str, RelatorioAuditoria] = {}
        for r in dados.RELATORIOS:
            relatorios[r["casa"]], _ = RelatorioAuditoria.objects.update_or_create(
                unidade=casas[r["casa"]],
                numero=r["numero"],
                defaults={
                    "data_visita": r["visita"],
                    "data_emissao": r["emissao"],
                    "responsavel_tecnico": dados.RESPONSAVEL_TECNICO,
                    "acompanhante": r.get("acompanhante", ""),
                    "recebido": r.get("recebido", True),
                    "sintese": r.get("sintese", ""),
                },
            )
        return relatorios

    def _checklist_campo(self, relatorios: dict[str, RelatorioAuditoria]) -> None:
        pontos: dict[int, PontoVerificacao] = {}
        for indice, (pergunta, referencia) in enumerate(dados.PONTOS_VERIFICACAO, start=1):
            pontos[indice], _ = PontoVerificacao.objects.update_or_create(
                pergunta=pergunta, defaults={"ordem": indice, "referencia_legal": referencia}
            )
        for casa, respostas in dados.RESPOSTAS_CAMPO.items():
            relatorio = relatorios.get(casa)
            if not relatorio:
                continue
            for indice, (resultado, observacao) in respostas.items():
                RespostaCampo.objects.update_or_create(
                    relatorio=relatorio,
                    ponto=pontos[indice],
                    defaults={"resultado": resultado, "observacao": observacao},
                )

    def _documentos(self, casas: dict[str, Unidade]) -> None:
        stx = Usuario.objects.filter(perfil="CONSULTORIA").first()
        for d in dados.DOCUMENTOS:
            tipo = TipoDocumento.objects.get(codigo=d["tipo"])
            unidade = casas[d["casa"]]
            Documento.objects.update_or_create(
                unidade=unidade,
                tipo=tipo,
                versao=1,
                defaults={
                    "identificacao": d["identificacao"],
                    "data_emissao": d["emissao"],
                    "data_vencimento": d.get("vencimento"),
                    "situacao": d.get("situacao", SituacaoDocumento.VALIDADO),
                    "versao_corrente": True,
                    "observacao": d.get("observacao", ""),
                    "validado_por": stx if d.get("situacao") != SituacaoDocumento.AGUARDANDO else None,
                },
            )

    def _condicionantes(self, casas: dict[str, Unidade]) -> None:
        for c in dados.CONDICIONANTES:
            Condicionante.objects.update_or_create(
                unidade=casas[c["casa"]],
                descricao=c["descricao"],
                defaults={
                    "licenca": c["licenca"],
                    "prazo": c["prazo"],
                    "responsavel": c["responsavel"],
                    "situacao": c["situacao"],
                },
            )

    def _nao_conformidades(self, casas, relatorios) -> None:
        for n in dados.NAO_CONFORMIDADES:
            NaoConformidade.objects.update_or_create(
                codigo=n["codigo"],
                defaults={
                    "unidade": casas[n["casa"]],
                    "relatorio": relatorios.get(n["casa"]),
                    "origem": n["origem"],
                    "data_abertura": n["abertura"],
                    "descricao": n["descricao"],
                    "requisito_violado": n["requisito"],
                    "gravidade": n["gravidade"],
                    "situacao": n["situacao"],
                    "o_que": n["o_que"],
                    "por_que": n["por_que"],
                    "onde": n["onde"],
                    "quem": n["quem"],
                    "prazo": n["prazo"],
                    "como": n["como"],
                    "quanto": n["quanto"],
                    "custo_estimado": n.get("custo"),
                },
            )

    def _residuos(self, casas: dict[str, Unidade]) -> None:
        for r in dados.RESIDUOS:
            MovimentacaoResiduo.objects.update_or_create(
                unidade=casas[r["casa"]],
                residuo=r["residuo"],
                data_movimentacao=r["data"],
                defaults={
                    "classe": r["classe"],
                    "codigo_ibama": r.get("codigo", ""),
                    "quantidade": r.get("quantidade"),
                    "unidade_medida": r.get("medida", "kg"),
                    "destinacao": r["destinacao"],
                    "destinador": r.get("destinador", ""),
                    "numero_mtr": r.get("mtr", ""),
                    "numero_cdf": r.get("cdf", ""),
                    "observacao": r.get("observacao", ""),
                },
            )
