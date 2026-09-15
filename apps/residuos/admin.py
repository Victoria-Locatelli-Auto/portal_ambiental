from django.contrib import admin

from apps.residuos.models import MovimentacaoResiduo


@admin.register(MovimentacaoResiduo)
class MovimentacaoResiduoAdmin(admin.ModelAdmin):
    list_display = (
        "residuo", "unidade", "classe", "quantidade", "unidade_medida",
        "destinador", "numero_mtr", "numero_cdf", "rastreavel", "data_movimentacao",
    )
    list_filter = ("classe", "unidade", "data_movimentacao")
    search_fields = ("residuo", "destinador", "numero_mtr", "numero_cdf")
    date_hierarchy = "data_movimentacao"

    @admin.display(boolean=True, description="MTR + CDF")
    def rastreavel(self, obj):
        return obj.rastreavel
