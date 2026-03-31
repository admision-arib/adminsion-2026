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
                    # =====================================
                    # TRANSACCIÓN BD
                    # =====================================
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

                        # -------------------------------------
                        # GOOGLE DRIVE
                        # -------------------------------------
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

                    # =====================================
                    # GENERAR PDF + ENVIAR SENDGRID
                    # =====================================
                    correo_enviado = True

                    try:
                        # ✅ 1. Generar PDF (ruta)
                        pdf_path = generar_ficha_postulante_pdf(inscripcion)

                        # ✅ 2. Guardar ruta en BD (CRÍTICO)
                        inscripcion.ficha_pdf_path = pdf_path
                        inscripcion.save(update_fields=["ficha_pdf_path"])

                        # ✅ 3. Leer PDF desde disco
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()

                        # ✅ 4. Enviar correo por SendGrid (HTTP)
                        enviar_ficha_postulante(inscripcion, pdf_bytes)

                    except Exception as e:
                        correo_enviado = False
                        logger.exception(
                            f"Error enviando ficha de inscripción {inscripcion.id}"
                        )

                    # ✅ 5. Guardar estado del correo
                    inscripcion.correo_enviado = correo_enviado
                    inscripcion.save(update_fields=["correo_enviado"])

                    # ✅ Guardar ID para vista de confirmación
                    request.session["ultima_inscripcion_id"] = inscripcion.id

                    if correo_enviado:
                        messages.success(
                            request,
                            "✅ Inscripción registrada correctamente. "
                            "La ficha fue enviada a su correo electrónico."
                        )
                    else:
                        messages.warning(
                            request,
                            "✅ Inscripción registrada correctamente. "
                            "⚠️ No se pudo enviar el correo en este momento."
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



