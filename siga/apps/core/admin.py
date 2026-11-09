from django.contrib import admin

from apps.core.models import LogAuditoria


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("criado_em", "usuario_nome", "acao", "objeto")
    list_filter = ("acao", "entidade", "criado_em")
    search_fields = ("usuario_nome", "objeto", "detalhe")
    date_hierarchy = "criado_em"
    readonly_fields = tuple(f.name for f in LogAuditoria._meta.fields)

    def has_add_permission(self, request):  # noqa: ARG002
        return False

    def has_change_permission(self, request, obj=None):  # noqa: ARG002
        return False

    def has_delete_permission(self, request, obj=None):  # noqa: ARG002
        return False
