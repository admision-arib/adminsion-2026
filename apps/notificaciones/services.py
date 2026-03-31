import base64
import os
import requests
from decouple import config


SENDGRID_API_KEY = config("SENDGRID_API_KEY")
SENDGRID_ENDPOINT = "https://api.sendgrid.com/v3/mail/send"


def enviar_ficha_postulante(inscripcion, pdf_bytes):
    """
    Envía la ficha de postulante por correo usando SendGrid API (HTTP).
    Reemplaza completamente SMTP / EmailMessage.
    """

    if not SENDGRID_API_KEY:
        raise RuntimeError("SENDGRID_API_KEY no está configurada")

    postulante = inscripcion.postulante

    # ✅ Codificar PDF a Base64 (requisito SendGrid)
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

    asunto = f"Ficha de postulante - {inscripcion.numero_inscripcion}"

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

    payload = {
        "personalizations": [
            {
                "to": [{"email": postulante.correo_electronico}],
                "subject": asunto
            }
        ],
        "from": {
            "email": "admision@iestparib.edu.pe",
            "name": "Sistema de Admisión Institucional"
        },
        "content": [
            {
                "type": "text/plain",
                "value": cuerpo
            }
        ],
        "attachments": [
            {
                "content": pdf_base64,
                "type": "application/pdf",
                "filename": f"ficha_{inscripcion.numero_inscripcion}.pdf",
                "disposition": "attachment"
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        SENDGRID_ENDPOINT,
        json=payload,
        headers=headers,
        timeout=10  # ✅ importante en Render
    )

    response.raise_for_status()