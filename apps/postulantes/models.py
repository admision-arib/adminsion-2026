from django.conf import settings
from django.db import models
from apps.admision.models import Convocatoria, ModalidadPostulacion, ProgramaEstudio


class Postulante(models.Model):
    class TipoDocumento(models.TextChoices):
        DNI = "DNI", "DNI"
        PASAPORTE = "PASAPORTE", "Pasaporte"
        CE = "CE", "Carné de Extranjería"

    class Sexo(models.TextChoices):
        MASCULINO = "M", "Masculino"
        FEMENINO = "F", "Femenino"

    class IdiomaMaterno(models.TextChoices):
        CASTELLANO = "CASTELLANO", "Castellano"
        QUECHUA = "QUECHUA", "Quechua"
        AIMARA = "AIMARA", "Aimara"
        ASHANINKA = "ASHANINKA", "Asháninka"
        OTRO = "OTRO", "Otro"

    class GestionInstitucion(models.TextChoices):
        PUBLICA = "PUBLICA", "Pública"
        PRIVADA = "PRIVADA", "Privada"

    # Datos personales
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100)
    nombres = models.CharField(max_length=150)
    tipo_documento = models.CharField(max_length=20, choices=TipoDocumento.choices, default=TipoDocumento.DNI)
    numero_documento = models.CharField(max_length=20, unique=True)
    sexo = models.CharField(max_length=1, choices=Sexo.choices)
    correo_electronico = models.EmailField()
    celular = models.CharField(max_length=20)
    idioma_materno = models.CharField(max_length=20, choices=IdiomaMaterno.choices, default=IdiomaMaterno.CASTELLANO)
    idioma_materno_otro = models.CharField(max_length=100, blank=True)

    # Lugar y fecha de nacimiento
    lugar_nacimiento = models.CharField(max_length=120)
    distrito_nacimiento = models.CharField(max_length=120)
    provincia_nacimiento = models.CharField(max_length=120)
    departamento_nacimiento = models.CharField(max_length=120)
    pais_nacimiento = models.CharField(max_length=120, default="Perú")
    fecha_nacimiento = models.DateField()

    # Tutor si es menor de edad
    es_menor_edad = models.BooleanField(default=False)
    tutor_apellidos = models.CharField(max_length=150, blank=True)
    tutor_nombres = models.CharField(max_length=150, blank=True)
    tutor_numero_documento = models.CharField(max_length=20, blank=True)
    tutor_tipo_parentesco = models.CharField(max_length=100, blank=True)

    # Información académica
    institucion_procedencia = models.CharField(max_length=255)
    anio_egreso = models.PositiveIntegerField()
    gestion_institucion = models.CharField(
        max_length=20,
        choices=GestionInstitucion.choices
    )
    direccion_institucion = models.CharField(max_length=255)
    distrito_institucion = models.CharField(max_length=120)
    provincia_institucion = models.CharField(max_length=120)
    departamento_institucion = models.CharField(max_length=120)
    pais_institucion = models.CharField(max_length=120, default="Perú")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "postulante"
        verbose_name_plural = "postulantes"
        ordering = ["apellido_paterno", "apellido_materno", "nombres"]

    def __str__(self):
        return f"{self.apellido_paterno} {self.apellido_materno}, {self.nombres}"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}".strip()


class Inscripcion(models.Model):
    class Estado(models.TextChoices):
        #BORRADOR = "BORRADOR", "Borrador"
        #ENVIADA = "ENVIADA", "Enviada"
        REGISTRADO = "REGISTRADO", "Registrado"
        OBSERVADO = "OBSERVADO", "Observado"
        VALIDADO = "VALIDADO", "Validado"
    #

    postulante = models.ForeignKey(Postulante, on_delete=models.CASCADE, related_name="inscripciones")
    convocatoria = models.ForeignKey(Convocatoria, on_delete=models.PROTECT, related_name="inscripciones")
    modalidad = models.ForeignKey(ModalidadPostulacion, on_delete=models.PROTECT)

    primera_opcion_programa = models.ForeignKey(
        ProgramaEstudio,
        on_delete=models.PROTECT,
        related_name="inscripciones_primera_opcion"
    )
    segunda_opcion_programa = models.ForeignKey(
        ProgramaEstudio,
        on_delete=models.PROTECT,
        related_name="inscripciones_segunda_opcion",
        null=True,
        blank=True
    )
    medio_informacion_admision = models.CharField(max_length=150, blank=True)
    codigo_voucher_pago = models.CharField(max_length=50, unique=True)
    codigo_postulante = models.CharField(max_length=30, unique=True)
    numero_inscripcion = models.CharField(max_length=30, unique=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.REGISTRADO)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_validacion = models.DateTimeField(null=True, blank=True)
    bloqueada = models.BooleanField(default=False)
    observaciones_generales = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    correo_enviado = models.BooleanField(default=False,verbose_name="Correo enviado")
    #ficha_pdf_path = models.CharField(max_length=255,blank=True,null=True)
    ficha_drive_id = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )
    ficha_drive_url = models.URLField(
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "inscripción"
        verbose_name_plural = "inscripciones"
        ordering = ["-fecha_creacion"]
        constraints = [
            models.UniqueConstraint(fields=["postulante", "convocatoria"], name="unique_postulante_convocatoria"),
        ]

    def __str__(self):
        return f"{self.numero_inscripcion} - {self.postulante.nombre_completo}"