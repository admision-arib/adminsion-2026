
# views_validacion.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .models import Inscripcion, DocumentoInscripcion
from apps.usuarios.models import Usuario


def es_validador(user):
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(es_validador)

def lista_inscripciones_validacion(request):
    inscripciones = Inscripcion.objects.filter(
        estado__in=[
            Inscripcion.Estado.REGISTRADO,
            Inscripcion.Estado.OBSERVADO,
        ]
    )

    return render(
        request,
        "validacion/lista_inscripciones.html",
        {"inscripciones": inscripciones}

    )

@login_required
@user_passes_test(es_validador)
def revisar_inscripcion(request, inscripcion_id):
    inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id)
    documentos = inscripcion.documentos.select_related("tipo_documento")

    if request.method == "POST":
        hay_observaciones = False

        for doc in documentos:
            valido = request.POST.get(f"valido_{doc.id}") == "on"
            observacion = request.POST.get(f"observacion_{doc.id}", "").strip()

            doc.valido = valido
            doc.observacion = observacion

            if not valido:
                hay_observaciones = True

            doc.save()

        if hay_observaciones:
            inscripcion.estado = Inscripcion.Estado.OBSERVADO
            inscripcion.bloqueada = False
        else:
            inscripcion.estado = Inscripcion.Estado.VALIDADO
            inscripcion.fecha_validacion = timezone.now()
            inscripcion.bloqueada = True

        inscripcion.save()
        return redirect("panel:dashboard")

    return render(
        request,
        "validacion/revisar_inscripcion.html",
        {
            "inscripcion": inscripcion,
            "documentos": documentos,
        }
    )