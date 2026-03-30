from django import forms
from django.contrib.auth import authenticate
from .models import Usuario



class FormularioInicioSesion(forms.Form):
    email = forms.EmailField(label="Correo electrónico")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            usuario = authenticate(username=email.lower(), password=password)
            if not usuario:
                raise forms.ValidationError("Credenciales inválidas.")
            if not usuario.is_active:
                raise forms.ValidationError("La cuenta no está activa.")
            cleaned_data["usuario"] = usuario
        return cleaned_data