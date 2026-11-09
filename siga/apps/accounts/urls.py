from django.urls import path

from apps.accounts import views

app_name = "administracao"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("tipos-documentais/", views.tipos_documento, name="tipos"),
    path("tipos-documentais/novo/", views.tipo_criar, name="tipo_criar"),
    path("tipos-documentais/<uuid:uuid>/editar/", views.tipo_editar, name="tipo_editar"),
    path("tipos-documentais/<uuid:uuid>/alternar/", views.tipo_alternar, name="tipo_alternar"),
    path("temas-legais/", views.temas_legais, name="temas"),
    path("temas-legais/novo/", views.tema_criar, name="tema_criar"),
    path("temas-legais/<int:pk>/editar/", views.tema_editar, name="tema_editar"),
    path("temas-legais/<int:pk>/alternar/", views.tema_alternar, name="tema_alternar"),
    path("usuarios/", views.usuarios, name="usuarios"),
    path("usuarios/novo/", views.usuario_criar, name="usuario_criar"),
    path("usuarios/<int:pk>/editar/", views.usuario_editar, name="usuario_editar"),
    path("usuarios/<int:pk>/alternar/", views.usuario_alternar, name="usuario_alternar"),
    path("modelos-email/", views.modelos_email, name="modelos_email"),
    path(
        "modelos-email/<int:pk>/editar/",
        views.modelo_email_editar,
        name="modelo_email_editar",
    ),
]
