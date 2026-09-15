from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "entrar/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
    path("api/", include("config.api")),
    path("sistema/", include("apps.accounts.urls", namespace="administracao")),
    path("", include("apps.dashboard.urls", namespace="dashboard")),
    path("compliance/", include("apps.compliance.urls", namespace="compliance")),
    path("notificacoes/", include("apps.notificacoes.urls", namespace="notificacoes")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "SIGA - Administracao"
admin.site.site_title = "SIGA"
admin.site.index_title = "Sistema Integrado de Gestao Ambiental - MCM"
