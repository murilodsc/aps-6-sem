from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("capturar/", views.capturar_foto, name="capturar_foto"),
    path("salvar-foto/", views.salvar_foto, name="salvar_foto"),
]
