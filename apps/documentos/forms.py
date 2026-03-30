from django import forms


class FormularioDocumentoInscripcion(forms.Form):
    archivo = forms.FileField(required=False)

    def clean_archivo(self):
        archivo = self.cleaned_data.get("archivo")
        if not archivo:
            return archivo

        extensiones_validas = [".pdf", ".jpg", ".jpeg", ".png"]
        nombre = archivo.name.lower()

        if not any(nombre.endswith(ext) for ext in extensiones_validas):
            raise forms.ValidationError("Solo se permiten archivos PDF, JPG, JPEG o PNG.")

        if archivo.size > 5 * 1024 * 1024:
            raise forms.ValidationError("El archivo no debe superar los 5 MB.")
        return archivo