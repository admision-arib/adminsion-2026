from django.urls import path
from . import views

app_name = "postulantes"

urlpatterns = [
    path("registro-inscripcion/", views.registrar_inscripcion, name="registrar_inscripcion"),
    path("confirmacion-inscripcion/", views.confirmacion_inscripcion, name="confirmacion_inscripcion"),

]