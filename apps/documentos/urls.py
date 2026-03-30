# validacion/urls.py
from django.urls import path
from . import views

app_name = "validacion"

urlpatterns = [
    path(
        "inscripciones/",
        views.lista_inscripciones_validacion,
        name="lista_inscripciones"
    ),
    path(
        "inscripcion/<int:inscripcion_id>/",
        views.revisar_inscripcion,
        name="revisar_inscripcion"
    ),
]