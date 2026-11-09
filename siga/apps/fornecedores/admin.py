from django.contrib import admin

from apps.fornecedores.models import Contrato, Fornecedor


class ContratoInline(admin.TabularInline):
    model = Contrato
    extra = 0


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ("razao_social", "cnpj_cpf", "servico_fornecido", "ativo")
    list_filter = ("ativo",)
    search_fields = ("razao_social", "nome_fantasia", "cnpj_cpf")
    inlines = (ContratoInline,)


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ("numero", "fornecedor", "data_inicio", "data_fim", "situacao")
    list_filter = ("situacao",)
    search_fields = ("numero", "fornecedor__razao_social")

