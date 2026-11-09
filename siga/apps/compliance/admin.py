from django.contrib import admin

from apps.compliance.forms import DocumentoAdminForm
from apps.compliance.models import (
    Condicionante,
    Documento,
    NormaLegal,
    AnexoProcessoRenovacao,
    ProcessoRenovacao,
    TemaLegalCadastro,
    TipoDocumento,
)


@admin.register(TemaLegalCadastro)
class TemaLegalCadastroAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "ordem", "ativo")
    list_filter = ("ativo",)
    search_fields = ("codigo", "nome")
    ordering = ("ordem", "nome")


@admin.register(NormaLegal)
class NormaLegalAdmin(admin.ModelAdmin):
    list_display = ("identificacao", "esfera", "objeto")
    list_filter = ("esfera",)
    search_fields = ("identificacao", "objeto")


@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo", "nome", "tema", "cor_agenda", "periodicidade_meses", "dias_alerta",
        "aplicabilidade", "responsavel_execucao", "ativo",
    )
    list_filter = ("tema", "cor_agenda", "aplicabilidade", "responsavel_execucao", "ativo")
    search_fields = ("codigo", "nome", "base_legal")
    filter_horizontal = ("normas",)
    ordering = ("ordem", "codigo")
    fieldsets = (
        ("Identificacao", {"fields": ("codigo", "nome", "tema", "cor_agenda", "ordem", "ativo")}),
        (
            "Prazo e alerta",
            {
                "fields": ("periodicidade_meses", "dias_alerta"),
                "description": "Periodicidade 0 = documento por evento, sem validade fixa.",
            },
        ),
        ("Aplicacao", {"fields": ("aplicabilidade", "responsavel_execucao")}),
        ("Fundamento", {"fields": ("base_legal", "normas", "nota_tecnica")}),
        (
            "Checklist da casa",
            {
                "fields": ("instrucao",),
                "description": "Texto em linguagem direta exibido para a coordenadora.",
            },
        ),
    )


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    form = DocumentoAdminForm
    list_display = (
        "identificacao", "unidade", "tipo", "data_emissao", "data_vencimento",
        "situacao", "versao", "versao_corrente",
    )
    list_filter = ("situacao", "versao_corrente", "unidade", "tipo__tema")
    search_fields = ("identificacao", "unidade__nome", "tipo__nome")
    date_hierarchy = "data_emissao"
    autocomplete_fields = ("unidade", "tipo") if False else ()
    readonly_fields = ("versao", "validado_em")


@admin.register(ProcessoRenovacao)
class ProcessoRenovacaoAdmin(admin.ModelAdmin):
    list_display = ("tipo", "unidade", "situacao", "data_inicio", "prazo", "numero_protocolo")
    list_filter = ("situacao", "unidade")
    search_fields = ("tipo__nome", "unidade__nome", "numero_protocolo")
    filter_horizontal = ("documentos",)


@admin.register(AnexoProcessoRenovacao)
class AnexoProcessoRenovacaoAdmin(admin.ModelAdmin):
    list_display = ("arquivo", "processo", "enviado_por", "criado_em")
    list_filter = ("processo__unidade",)
    search_fields = ("arquivo", "processo__tipo__nome", "processo__unidade__nome")


@admin.register(Condicionante)
class CondicionanteAdmin(admin.ModelAdmin):
    list_display = ("unidade", "licenca", "prazo", "responsavel", "situacao", "em_atraso")
    list_filter = ("situacao", "unidade")
    search_fields = ("descricao", "licenca")

    @admin.display(boolean=True, description="Em atraso")
    def em_atraso(self, obj):
        return obj.em_atraso
