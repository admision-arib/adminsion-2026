from django.urls import path
from . import views

app_name = "panel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("postulantes/", views.lista_postulantes, name="lista_postulantes"),
    path("postulantes/exportar-excel/", views.exportar_postulantes_excel, name="exportar_postulantes_excel"),
    path("postulantes/<int:inscripcion_id>/", views.detalle_postulante, name="detalle_postulante"),
    path("postulantes/<int:inscripcion_id>/ficha-completa/", views.generar_ficha_completa, name="generar_ficha_completa"),
    path("postulantes/<int:inscripcion_id>/reenviar-ficha/", views.reenviar_ficha, name="reenviar_ficha"),
]