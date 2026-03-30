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
    convocatoria_automatica = Convocatoria.objects.filter(
        anio=2026, activa=True
    ).first()

    modalidad_automatica = ModalidadPostulacion.objects.filter(
        nombre__iexact="examen virtual",
        activa=True
    ).first()

    if not convocatoria_automatica:
        messages.error(
            request,
            "No existe una convocatoria activa para el año 2026."
        )
        return redirect("core:inicio")

    if not modalidad_automatica:
        messages.error(
            request,
            "No existe una modalidad activa llamada Examen Virtual."
        )
        return redirect("core:inicio")

    tipos_documento = TipoDocumento.objects.filter(
        activo=True
    ).order_by("nombre")

    faltantes = []

    if request.method == "POST":
        form_postulante = FormularioPostulante(request.POST)
        form_inscripcion = FormularioInscripcion(request.POST)

        # ✅ Validación documentos obligatorios
        for tipo in tipos_documento.filter(obligatorio=True):
            archivo = request.FILES.get(f"{tipo.codigo}-archivo")
            if not archivo:
                faltantes.append(tipo.nombre)

        if form_postulante.is_valid() and form_inscripcion.is_valid():

            if faltantes:
                messages.error(
                    request,
                    "Faltan documentos obligatorios: "
                    + ", ".join(faltantes)
                )
            else:
                try:
                    # ===============================
                    # ✅ GUARDADO BD (TRANSACTION)
                    # ===============================
                    with transaction.atomic():
                        postulante = form_postulante.save()

                        inscripcion = form_inscripcion.save(commit=False)
                        inscripcion.postulante = postulante
                        inscripcion.convocatoria = convocatoria_automatica
                        inscripcion.modalidad = modalidad_automatica
                        inscripcion.estado = Inscripcion.Estado.REGISTRADO
                        inscripcion.save()

                        completar_codigos_inscripcion(inscripcion)

                        # ===============================
                        # ✅ GOOGLE DRIVE
                        # ===============================
                        drive = ServicioGoogleDrive()
                        carpeta_postulante = drive.crear_estructura_postulante(
                            anio=convocatoria_automatica.anio,
                            modalidad=modalidad_automatica.nombre,
                            numero_documento=postulante.numero_documento,
                            nombres=postulante.nombres,
                            apellido_paterno=postulante.apellido_paterno,
                            apellido_materno=postulante.apellido_materno,
                        )

                        for tipo in tipos_documento:
                            archivo = request.FILES.get(
                                f"{tipo.codigo}-archivo"
                            )
                            if archivo:
                                nombre_destino = construir_nombre_documento(
                                    tipo.codigo,
                                    postulante.numero_documento,
                                    archivo
                                )

                                archivo_drive = drive.subir_archivo(
                                    archivo=archivo,
                                    nombre_destino=nombre_destino,
                                    parent_id=carpeta_postulante["id"]
                                )

                                DocumentoInscripcion.objects.update_or_create(
                                    inscripcion=inscripcion,
                                    tipo_documento=tipo,
                                    defaults={
                                        "nombre_original": archivo.name,
                                        "nombre_guardado": nombre_destino,
                                        "mime_type": getattr(
                                            archivo, "content_type", ""
                                        ),
                                        "tamano_bytes": archivo.size,
                                        "drive_file_id": archivo_drive.get("id", ""),
                                        "drive_url": archivo_drive.get(
                                            "webViewLink", ""
                                        ),
                                        "drive_folder_id": carpeta_postulante["id"],
                                        "valido": True,
                                    }
                                )

                    # ======================================
                    # ✅ CORREO (NO BLOQUEANTE)
                    # ======================================
                    correo_enviado = True

                    try:
                        pdf_bytes = generar_ficha_postulante_pdf(inscripcion)
                        enviar_ficha_postulante(inscripcion, pdf_bytes)
                    except Exception as e:
                        correo_enviado = False
                        logger.error(
                            f"Error enviando ficha inscripción "
                            f"{inscripcion.id}: {str(e)}"
                        )

                    # ======================================
                    # ✅ MENSAJE FINAL AL POSTULANTE
                    # ======================================
                    if correo_enviado:
                        messages.success(
                            request,
                            "Su inscripción fue registrada correctamente. "
                            "La ficha de postulante fue enviada a su correo electrónico."
                        )
                    else:
                        messages.warning(
                            request,
                            "Su inscripción fue registrada correctamente. "
                            "En este momento no se pudo enviar el correo, "
                            "pero la institución podrá reenviar su ficha."
                        )

                    return redirect(
                        "postulantes:confirmacion_inscripcion"
                    )

                except IntegrityError as e:
                    logger.warning(f"Error BD inscripción duplicada: {e}")
                    messages.error(
                        request,
                        "Ya existe una inscripción registrada con los datos ingresados."
                    )
                except Exception as e:
                    logger.exception("Error general registrando inscripción")
                    messages.error(
                        request,
                        "Ocurrió un error inesperado. "
                        "Comuníquese con la institución."
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
            "convocatoria_automatica": convocatoria_automatica,
            "modalidad_automatica": modalidad_automatica,
            "faltantes": faltantes,
        }
    )


def confirmacion_inscripcion(request):
    return render(request, "postulantes/confirmacion_inscripcion.html")

