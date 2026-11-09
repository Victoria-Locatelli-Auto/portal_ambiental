from django.urls import path

from apps.notificacoes import views

app_name = "notificacoes"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("<uuid:uuid>/abrir/", views.abrir, name="abrir"),
    path("marcar-todas-lidas/", views.marcar_todas_lidas, name="marcar_todas_lidas"),
]
