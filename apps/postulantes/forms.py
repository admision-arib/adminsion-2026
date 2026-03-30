from django import forms
from .models import Postulante, Inscripcion


class FormularioPostulante(forms.ModelForm):
    class Meta:
        model = Postulante
        fields = [
            "apellido_paterno",
            "apellido_materno",
            "nombres",
            "tipo_documento",
            "numero_documento",
            "sexo",
            "correo_electronico",
            "celular",
            "idioma_materno",
            "idioma_materno_otro",
            "lugar_nacimiento",
            "distrito_nacimiento",
            "provincia_nacimiento",
            "departamento_nacimiento",
            "pais_nacimiento",
            "fecha_nacimiento",
            "es_menor_edad",
            "tutor_apellidos",
            "tutor_nombres",
            "tutor_numero_documento",
            "tutor_tipo_parentesco",
            "institucion_procedencia",
            "anio_egreso",
            "gestion_institucion",
            "direccion_institucion",
            "distrito_institucion",
            "provincia_institucion",
            "departamento_institucion",
            "pais_institucion",
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_numero_documento(self):
        numero_documento = self.cleaned_data["numero_documento"].strip()
        tipo_documento = self.cleaned_data.get("tipo_documento")

        # Validación de formato DNI
        if tipo_documento == Postulante.TipoDocumento.DNI:
            if len(numero_documento) != 8 or not numero_documento.isdigit():
                raise forms.ValidationError(
                    "El DNI debe tener exactamente 8 dígitos numéricos."
                )

        # ✅ Validación de unicidad DNI
        if Postulante.objects.filter(
                numero_documento=numero_documento
        ).exists():
            raise forms.ValidationError(
                "Ya existe una inscripción registrada con este número de documento."
            )

        return numero_documento

    def clean(self):
        cleaned_data = super().clean()

        idioma_materno = cleaned_data.get("idioma_materno")
        idioma_materno_otro = cleaned_data.get("idioma_materno_otro")
        es_menor_edad = cleaned_data.get("es_menor_edad")

        if idioma_materno == Postulante.IdiomaMaterno.OTRO and not idioma_materno_otro:
            self.add_error("idioma_materno_otro", "Debes especificar el idioma materno.")

        if es_menor_edad:
            for campo in ["tutor_apellidos", "tutor_nombres", "tutor_numero_documento", "tutor_tipo_parentesco"]:
                if not cleaned_data.get(campo):
                    self.add_error(campo, "Este campo es obligatorio para menores de edad.")

        return cleaned_data


class FormularioInscripcion(forms.ModelForm):
    class Meta:
        model = Inscripcion
        fields = [
            "primera_opcion_programa",
            "segunda_opcion_programa",
            "medio_informacion_admision",
            "codigo_voucher_pago",
        ]

    def clean_codigo_voucher_pago(self):
        codigo = self.cleaned_data.get("codigo_voucher_pago")

        if codigo and Inscripcion.objects.filter(
                codigo_voucher_pago=codigo
        ).exists():
            raise forms.ValidationError(
                "Este código de voucher ya ha sido registrado."
            )

        return codigo
