"""Roteamento da API REST."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.auditoria.api import NaoConformidadeViewSet
from apps.compliance.api import DocumentoViewSet, TipoDocumentoViewSet
from apps.organizacao.api import UnidadeViewSet
from apps.residuos.api import MovimentacaoResiduoViewSet

router = DefaultRouter()
router.register("unidades", UnidadeViewSet, basename="unidade")
router.register("tipos-documento", TipoDocumentoViewSet, basename="tipodocumento")
router.register("documentos", DocumentoViewSet, basename="documento")
router.register("nao-conformidades", NaoConformidadeViewSet, basename="naoconformidade")
router.register("residuos", MovimentacaoResiduoViewSet, basename="residuo")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("rest_framework.urls")),
]
