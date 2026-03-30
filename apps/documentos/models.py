from django.db import models
from apps.postulantes.models import Inscripcion


class TipoDocumento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=30, unique=True)
    obligatorio = models.BooleanField(default=True)
    extensiones_permitidas = models.CharField(max_length=100, default="pdf,jpg,jpeg,png")
    tamano_max_mb = models.PositiveIntegerField(default=5)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "tipo de documento"
        verbose_name_plural = "tipos de documento"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class DocumentoInscripcion(models.Model):
    inscripcion = models.ForeignKey(Inscripcion, on_delete=models.CASCADE, related_name="documentos")
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.PROTECT)
    nombre_original = models.CharField(max_length=255)
    nombre_guardado = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    tamano_bytes = models.BigIntegerField(default=0)
    drive_file_id = models.CharField(max_length=255, blank=True)
    drive_url = models.URLField(blank=True)
    drive_folder_id = models.CharField(max_length=255, blank=True)
    observacion = models.TextField(
        blank=True,
        help_text="Observación del validador si el documento no es válido"
    )
    valido = models.BooleanField(default=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "documento de inscripción"
        verbose_name_plural = "documentos de inscripción"
        ordering = ["-fecha_subida"]
        constraints = [
            models.UniqueConstraint(fields=["inscripcion", "tipo_documento"], name="unique_documento_por_tipo_inscripcion"),
        ]

    def __str__(self):
        return f"{self.tipo_documento.nombre} - {self.inscripcion.numero_inscripcion}"
