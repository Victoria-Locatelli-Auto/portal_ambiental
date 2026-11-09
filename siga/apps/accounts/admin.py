from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.accounts.models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("nome_completo", "email", "perfil", "unidade", "is_active")
    list_filter = ("perfil", "is_active", "unidade")
    search_fields = ("nome_completo", "email", "cargo")
    ordering = ("nome_completo",)
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Identificacao", {"fields": ("nome_completo", "cargo", "telefone")}),
        ("Acesso ao SIGA", {"fields": ("perfil", "unidade", "recebe_notificacoes")}),
        ("Permissoes Django", {"fields": ("is_active", "is_staff", "is_superuser", "groups")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "nome_completo",
                    "perfil",
                    "unidade",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
