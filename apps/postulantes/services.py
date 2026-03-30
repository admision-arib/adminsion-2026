from django.utils import timezone
from .models import Inscripcion


def generar_codigo_postulante(convocatoria_id, postulante_id):
    anio = timezone.now().year
    return f"POST-{anio}-{convocatoria_id:03d}-{postulante_id:06d}"


def generar_numero_inscripcion(convocatoria_id, postulante_id):
    anio = timezone.now().year
    return f"INS-{anio}-{convocatoria_id:03d}-{postulante_id:06d}"


def completar_codigos_inscripcion(inscripcion):
    if not inscripcion.codigo_postulante:
        inscripcion.codigo_postulante = generar_codigo_postulante(inscripcion.convocatoria_id, inscripcion.postulante_id)
    if not inscripcion.numero_inscripcion:
        inscripcion.numero_inscripcion = generar_numero_inscripcion(inscripcion.convocatoria_id, inscripcion.postulante_id)
    inscripcion.save(update_fields=["codigo_postulante", "numero_inscripcion"])
    return inscripcion