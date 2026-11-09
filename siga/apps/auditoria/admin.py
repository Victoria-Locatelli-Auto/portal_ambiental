from django.contrib import admin

from apps.auditoria.models import (
    NaoConformidade,
    PontoVerificacao,
    RelatorioAuditoria,
    RespostaCampo,
)


class RespostaCampoInline(admin.TabularInline):
    model = RespostaCampo
    extra = 0
    fields = ("ponto", "resultado", "observacao")


@admin.register(RelatorioAuditoria)
class RelatorioAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("numero", "unidade", "data_visita", "data_emissao", "recebido")
    list_filter = ("recebido", "unidade", "data_emissao")
    inlines = [RespostaCampoInline]


@admin.register(PontoVerificacao)
class PontoVerificacaoAdmin(admin.ModelAdmin):
    list_display = ("ordem", "pergunta", "referencia_legal")
    ordering = ("ordem",)


@admin.register(NaoConformidade)
class NaoConformidadeAdmin(admin.ModelAdmin):
    list_display = ("codigo", "unidade", "gravidade", "situacao", "prazo", "prazo_vencido")
    list_filter = ("gravidade", "situacao", "origem", "unidade")
    search_fields = ("codigo", "descricao", "requisito_violado")
    date_hierarchy = "data_abertura"
    fieldsets = (
        (
            "Identificacao",
            {
                "fields": (
                    "codigo", "unidade", "origem", "relatorio", "data_abertura",
                    "gravidade", "situacao",
                )
            },
        ),
        ("Desvio", {"fields": ("descricao", "requisito_violado")}),
        (
            "Plano de acao 5W2H",
            {
                "fields": (
                    "o_que", "por_que", "onde", "quem", "prazo", "como", "quanto",
                    "custo_estimado",
                )
            },
        ),
        ("Encerramento", {"fields": ("encerrada_em", "evidencia_encerramento", "responsavel")}),
    )


admin.site.register(RespostaCampo)
