from django.conf import settings
from django.core.mail import EmailMessage


def enviar_ficha_postulante(inscripcion, pdf_bytes):
    postulante = inscripcion.postulante

    asunto = f"Ficha de postulante - {inscripcion.numero_inscripcion}"
    destinatario = [postulante.correo_electronico]

    cuerpo = f"""
Estimado(a) {postulante.nombres}:

Su inscripción al proceso de admisión fue registrada correctamente.

Adjuntamos su ficha de postulante en formato PDF.

Datos principales:
- N.° de inscripción: {inscripcion.numero_inscripcion}
- Código de postulante: {inscripcion.codigo_postulante}
- Programa (1ra opción): {inscripcion.primera_opcion_programa.nombre}

Revise cuidadosamente su ficha y consérvela para el proceso de admisión.

Atentamente,
Sistema de Admisión Institucional
""".strip()

    email = EmailMessage(
        subject=asunto,
        body=cuerpo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=destinatario,
    )

    nombre_archivo = f"ficha_{inscripcion.numero_inscripcion}.pdf"
    email.attach(nombre_archivo, pdf_bytes, "application/pdf")
    email.send(fail_silently=False)