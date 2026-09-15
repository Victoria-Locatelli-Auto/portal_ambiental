from django.contrib import admin

from apps.organizacao.models import Unidade


@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nome",
        "uf",
        "cnpj",
        "potencial_poluidor",
        "tem_oficina",
        "tem_poco",
        "opera_em_posto",
        "responsavel_nome",
        "ultima_visita_tecnica",
    )
    list_filter = ("uf", "potencial_poluidor", "imovel", "tem_oficina", "tem_poco", "opera_em_posto")
    search_fields = ("nome", "cnpj", "municipio", "responsavel_nome")
    fieldsets = (
        ("Identificacao", {"fields": ("codigo", "nome", "cnpj", "uf", "municipio", "endereco")}),
        (
            "Caracterizacao",
            {"fields": ("atividade", "porte", "potencial_poluidor", "imovel")},
        ),
        (
            "Aplicabilidade de requisitos",
            {
                "fields": ("tem_oficina", "tem_poco", "opera_em_posto"),
                "description": "Estas flags definem quais documentos entram no checklist da casa.",
            },
        ),
        ("Orgaos licenciadores", {"fields": ("orgao_estadual", "orgao_municipal")}),
        (
            "Responsavel local",
            {"fields": ("responsavel_nome", "responsavel_cargo", "responsavel_email")},
        ),
        ("Auditoria", {"fields": ("ultima_visita_tecnica", "diagnostico")}),
    )
