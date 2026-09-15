from django.contrib import admin

from apps.notificacoes.models import ModeloEmail, Notificacao, NotificacaoSistema


@admin.register(ModeloEmail)
class ModeloEmailAdmin(admin.ModelAdmin):
    list_display = ("tipo", "ativo", "atualizado_em")
    list_filter = ("ativo",)


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ("criado_em", "tipo", "unidade", "destinatario", "assunto", "situacao")
    list_filter = ("tipo", "situacao", "unidade")
    search_fields = ("destinatario", "assunto")
    date_hierarchy = "criado_em"
    readonly_fields = ("chave_idempotencia", "enviada_em", "corpo")


@admin.register(NotificacaoSistema)
class NotificacaoSistemaAdmin(admin.ModelAdmin):
    list_display = ("criado_em", "usuario", "tipo", "unidade", "titulo", "lida_em")
    list_filter = ("tipo", "unidade", "lida_em")
    search_fields = ("usuario__nome_completo", "usuario__email", "titulo")
    readonly_fields = ("origem_email", "mensagem", "link")
