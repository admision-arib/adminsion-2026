from django.urls import path
from . import views

app_name = "usuarios"

urlpatterns = [
    #path("registrarse/", views.registrar_usuario, name="registrar"),
    path("iniciar-sesion/", views.iniciar_sesion, name="iniciar_sesion"),
    path("cerrar-sesion/", views.cerrar_sesion, name="cerrar_sesion"),
]