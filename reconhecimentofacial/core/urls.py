from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("login/facial/", views.login_facial_view, name="login_facial"),
    path("reconhecer-face/", views.reconhecer_face, name="reconhecer_face"),
    path("logout/", views.logout_view, name="logout"),
    
    # CRUD Propriedades Rurais
    path("propriedades/", views.propriedades_list, name="propriedades_list"),
    path("propriedades/nova/", views.propriedade_create, name="propriedade_create"),
    path("propriedades/<int:pk>/", views.propriedade_detail, name="propriedade_detail"),
    path("propriedades/<int:pk>/editar/", views.propriedade_update, name="propriedade_update"),
    path("propriedades/<int:pk>/deletar/", views.propriedade_delete, name="propriedade_delete"),
    
    # CRUD Usuários
    path("usuarios/", views.usuarios_list, name="usuarios_list"),
    path("usuarios/novo/", views.usuario_create, name="usuario_create"),
    path("usuarios/<int:pk>/", views.usuario_detail, name="usuario_detail"),
    path("usuarios/<int:pk>/editar/", views.usuario_update, name="usuario_update"),
    path("usuarios/<int:pk>/deletar/", views.usuario_delete, name="usuario_delete"),
]
