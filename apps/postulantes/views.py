from django.contrib import messages
from django.shortcuts import redirect, render
from django.db import transaction, IntegrityError
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
        messages.error(request, "No existe una convocatoria o modalidad activa.")
        return redirect("core:inicio")

    tipos_documento = TipoDocumento.objects.filter(activo=True).order_by("nombre")
    faltantes = []

    if request.method == "POST":
        form_postulante = FormularioPostulante(request.POST)
        form_inscripcion = FormularioInscripcion(request.POST)

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
                    with transaction.atomic():

                        postulante = form_postulante.save()

                        inscripcion = form_inscripcion.save(commit=False)
                        inscripcion.postulante = postulante
                        inscripcion.convocatoria = convocatoria
                        inscripcion.modalidad = modalidad
                        inscripcion.estado = Inscripcion.Estado.REGISTRADO
                        inscripcion.save()

                        completar_codigos_inscripcion(inscripcion)

                        drive = ServicioGoogleDrive()
                        carpeta = drive.crear_estructura_postulante(
                            anio=convocatoria.anio,
                            modalidad=modalidad.nombre,
                            numero_documento=postulante.numero_documento,
                            nombres=postulante.nombres,
                            apellido_paterno=postulante.apellido_paterno,
                            apellido_materno=postulante.apellido_materno,
                        )

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

                    # ---------- ENVÍO SENDGRID ----------
                    correo_enviado = True
                    try:
                        pdf_bytes = generar_ficha_postulante_pdf(inscripcion)
                        enviar_ficha_postulante(inscripcion, pdf_bytes)
                    except Exception as e:
                        correo_enviado = False
                        logger.error(f"Error enviando correo: {e}")

                    inscripcion.correo_enviado = correo_enviado
                    inscripcion.save(update_fields=["correo_enviado"])

                    request.session["ultima_inscripcion_id"] = inscripcion.id

                    messages.success(
                        request,
                        "✔ Inscripción registrada correctamente. "
                        "La ficha fue enviada a su correo."
                    )

                    return redirect("postulantes:confirmacion_inscripcion")

                except IntegrityError:
                    messages.error(request, "Ya existe una inscripción con estos datos.")

                except Exception:
                    logger.exception("Error general")
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



