from django.contrib import messages
from django.shortcuts import redirect, render
from django.db import transaction, IntegrityError
import logging
import os

logger = logging.getLogger(__name__)

from apps.admision.models import Convocatoria, ModalidadPostulacion
from apps.documentos.models import TipoDocumento, DocumentoInscripcion
from apps.documentos.services.google_drive import ServicioGoogleDrive
from apps.documentos.services.utils import construir_nombre_documento

from apps.pdf.services import generar_ficha_postulante_pdf
from apps.notificaciones.services import enviar_ficha_postulante

from .forms import FormularioPostulante, FormularioInscripcion
from .models import Inscripcion
from .services import completar_codigos_inscripcion


# ============================================================
# REGISTRO DE INSCRIPCIÓN (PRODUCCIÓN – SENDGRID)
# ============================================================
from django.contrib import messages
from django.shortcuts import redirect, render
from django.db import transaction, IntegrityError
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)

from apps.admision.models import Convocatoria, ModalidadPostulacion
from apps.documentos.models import TipoDocumento, DocumentoInscripcion
from apps.documentos.services.google_drive import ServicioGoogleDrive
from apps.documentos.services.utils import construir_nombre_documento
from apps.pdf.services import generar_ficha_postulante_pdf
from apps.notificaciones.services import enviar_ficha_postulante

from .forms import FormularioPostulante, FormularioInscripcion
from .models import Inscripcion
from .services import completar_codigos_inscripcion


def registrar_inscripcion(request):

    convocatoria = Convocatoria.objects.filter(anio=2026, activa=True).first()
    modalidad = ModalidadPostulacion.objects.filter(
        nombre__iexact="examen virtual",
        activa=True
    ).first()

    if not convocatoria or not modalidad:
        messages.error(
            request,
            "No existe una convocatoria o modalidad activa."
        )
        return redirect("core:inicio")

    tipos_documento = TipoDocumento.objects.filter(activo=True).order_by("nombre")
    faltantes = []

    if request.method == "POST":
        form_postulante = FormularioPostulante(request.POST)
        form_inscripcion = FormularioInscripcion(request.POST)

        # ✅ Validar documentos obligatorios
        for tipo in tipos_documento.filter(obligatorio=True):
            if not request.FILES.get(f"{tipo.codigo}-archivo"):
                faltantes.append(tipo.nombre)

        if form_postulante.is_valid() and form_inscripcion.is_valid():

            if faltantes:
                messages.error(
                    request,
                    "Faltan documentos obligatorios: " + ", ".join(faltantes)
                )
            else:
                try:
                    # ===============================
                    # TRANSACCIÓN BD
                    # ===============================
                    with transaction.atomic():

                        postulante = form_postulante.save()

                        inscripcion = form_inscripcion.save(commit=False)
                        inscripcion.postulante = postulante
                        inscripcion.convocatoria = convocatoria
                        inscripcion.modalidad = modalidad
                        inscripcion.estado = Inscripcion.Estado.REGISTRADO
                        inscripcion.correo_enviado = False
                        inscripcion.save()

                        completar_codigos_inscripcion(inscripcion)

                        # ===============================
                        # GOOGLE DRIVE – CARPETA
                        # ===============================
                        drive = ServicioGoogleDrive()
                        carpeta = drive.crear_estructura_postulante(
                            anio=convocatoria.anio,
                            modalidad=modalidad.nombre,
                            numero_documento=postulante.numero_documento,
                            nombres=postulante.nombres,
                            apellido_paterno=postulante.apellido_paterno,
                            apellido_materno=postulante.apellido_materno,
                        )

                        # ===============================
                        # DOCUMENTOS DEL POSTULANTE
                        # ===============================
                        for tipo in tipos_documento:
                            archivo = request.FILES.get(f"{tipo.codigo}-archivo")
                            if archivo:
                                nombre_documento = construir_nombre_documento(
                                    tipo.codigo,
                                    postulante.numero_documento,
                                    archivo
                                )

                                archivo_drive = drive.subir_archivo(
                                    archivo=archivo,
                                    nombre_destino=nombre_documento,
                                    parent_id=carpeta["id"]
                                )

                                DocumentoInscripcion.objects.update_or_create(
                                    inscripcion=inscripcion,
                                    tipo_documento=tipo,
                                    defaults={
                                        "nombre_original": archivo.name,
                                        "nombre_guardado": nombre_documento,
                                        "mime_type": archivo.content_type,
                                        "tamano_bytes": archivo.size,
                                        "drive_file_id": archivo_drive.get("id"),
                                        "drive_url": archivo_drive.get("webViewLink"),
                                        "drive_folder_id": carpeta["id"],
                                        "valido": True,
                                    }
                                )

                        # ===============================
                        # FICHA PDF – DRIVE (CLAVE)
                        # ===============================
                        pdf_bytes = generar_ficha_postulante_pdf(inscripcion)

                        archivo_ficha = drive.subir_archivo(
                            archivo=ContentFile(pdf_bytes),
                            nombre_destino=f"ficha_{inscripcion.numero_inscripcion}.pdf",
                            parent_id=carpeta["id"]
                        )

                        # ✅ Guardar SOLO referencia (NO filesystem local)
                        inscripcion.ficha_drive_id = archivo_ficha.get("id")
                        inscripcion.ficha_drive_url = archivo_ficha.get("webViewLink")
                        inscripcion.save(
                            update_fields=["ficha_drive_id", "ficha_drive_url"]
                        )

                    # ===============================
                    # ENVÍO DE CORREO (SENDGRID)
                    # ===============================
                    try:
                        enviar_ficha_postulante(inscripcion, pdf_bytes)
                        inscripcion.correo_enviado = True
                    except Exception:
                        logger.exception(
                            f"Error enviando correo de inscripción {inscripcion.id}"
                        )
                        inscripcion.correo_enviado = False

                    inscripcion.save(update_fields=["correo_enviado"])

                    request.session["ultima_inscripcion_id"] = inscripcion.id

                    messages.success(
                        request,
                        "✅ Inscripción registrada correctamente. "
                        "📧 La ficha fue enviada a su correo electrónico."
                    )

                    return redirect("postulantes:confirmacion_inscripcion")

                except IntegrityError:
                    messages.error(
                        request,
                        "Ya existe una inscripción registrada con estos datos."
                    )

                except Exception:
                    logger.exception("Error general en registro de inscripción")
                    messages.error(
                        request,
                        "Ocurrió un error inesperado. Comuníquese con la institución."
                    )

    else:
        form_postulante = FormularioPostulante()
        form_inscripcion = FormularioInscripcion()

    return render(
        request,
        "postulantes/registrar_inscripcion.html",
        {
            "form_postulante": form_postulante,
            "form_inscripcion": form_inscripcion,
            "tipos_documento": tipos_documento,
            "faltantes": faltantes,
            "convocatoria_automatica": convocatoria,
            "modalidad_automatica": modalidad,
        }
    )


# ============================================================
# CONFIRMACIÓN DE INSCRIPCIÓN
# ============================================================
def confirmacion_inscripcion(request):
    inscripcion_id = request.session.get("ultima_inscripcion_id")
    inscripcion = Inscripcion.objects.filter(id=inscripcion_id).first()

    return render(
        request,
        "postulantes/confirmacion_inscripcion.html",
        {
            "correo_enviado": inscripcion.correo_enviado if inscripcion else False
        }
    )



