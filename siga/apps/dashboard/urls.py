from django.urls import path

from apps.dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.painel, name="painel"),
    path("checklist/", views.checklist_geral, name="checklist_geral"),
    path("checklist/<str:codigo>/", views.checklist_da_casa, name="checklist"),
    path("checklist/<str:codigo>/csv/", views.exportar_checklist, name="checklist_csv"),
    path("pendencias/", views.relatorio_pendencias, name="pendencias"),
]
