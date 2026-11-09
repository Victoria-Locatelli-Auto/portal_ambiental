from django.urls import path

from apps.fornecedores import views

app_name = "fornecedores"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("novo/", views.criar, name="criar"),
    path("<uuid:uuid>/", views.detalhe, name="detalhe"),
    path("<uuid:uuid>/editar/", views.editar, name="editar"),
    path("<uuid:uuid>/alternar/", views.alternar, name="alternar"),
    path("<uuid:uuid>/contratos/novo/", views.contrato_criar, name="contrato_criar"),
    path(
        "<uuid:uuid>/contratos/<uuid:contrato_uuid>/editar/",
        views.contrato_editar, name="contrato_editar",
    ),
]

