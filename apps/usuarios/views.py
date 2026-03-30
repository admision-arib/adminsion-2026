from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from .forms import FormularioInicioSesion
from apps.usuarios.models import Usuario



def iniciar_sesion(request):
    if request.user.is_authenticated:
        # Si ya está logueado, redirigir según rol
        if request.user.rol in [
            Usuario.Roles.VALIDADOR,
            Usuario.Roles.ADMINISTRADOR,
        ]:
            return redirect("panel:dashboard")
        return redirect("core:inicio")

    if request.method == "POST":
        form = FormularioInicioSesion(request.POST)

        if form.is_valid():
            usuario = form.cleaned_data["usuario"]
            login(request, usuario)

            messages.success(request, "Bienvenido al sistema.")

            # ✅ REDIRECCIÓN PROFESIONAL SEGÚN ROL
            if usuario.rol in [
                Usuario.Roles.VALIDADOR,
                Usuario.Roles.ADMINISTRADOR,
            ]:
                return redirect("panel:dashboard")
            else:
                return redirect("core:inicio")

    else:
        form = FormularioInicioSesion()

    return render(
        request,
        "usuarios/iniciar_sesion.html",
        {"form": form}
    )



def cerrar_sesion(request):
    logout(request)
    messages.info(request, "Has cerrado sesión.")
    return redirect("core:inicio")
