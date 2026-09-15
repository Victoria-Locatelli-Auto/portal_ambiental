from django.urls import path

from apps.compliance import views

app_name = "compliance"

urlpatterns = [
    path("documentos/", views.lista_documentos, name="documentos"),
    path("documentos/<uuid:uuid>/", views.detalhe_documento, name="detalhe_documento"),
    path("documentos/<uuid:uuid>/baixar/", views.baixar_documento, name="baixar_documento"),
    path(
        "documentos/<uuid:uuid>/visualizar/",
        views.visualizar_documento,
        name="visualizar_documento",
    ),
    path("documentos/<uuid:uuid>/validar/", views.validar_documento, name="validar"),
    path("documentos/<uuid:uuid>/rejeitar/", views.rejeitar_documento, name="rejeitar"),
    path("enviar/<str:codigo_casa>/<str:codigo_tipo>/", views.enviar_documento, name="enviar"),
    path("renovacoes/", views.lista_renovacoes, name="renovacoes"),
    path(
        "renovacoes/nova/<str:codigo_casa>/",
        views.criar_renovacao,
        name="renovacao_criar",
    ),
    path(
        "renovacoes/<uuid:uuid>/editar/",
        views.editar_renovacao,
        name="renovacao_editar",
    ),
    path(
        "renovacoes/anexos/<uuid:uuid>/baixar/",
        views.baixar_anexo_renovacao,
        name="renovacao_anexo_baixar",
    ),
]
