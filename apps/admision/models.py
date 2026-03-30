from django.db import models


class Convocatoria(models.Model):
    nombre = models.CharField(max_length=150)
    anio = models.PositiveIntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "convocatoria"
        verbose_name_plural = "convocatorias"
        ordering = ["-anio", "-fecha_inicio"]

    def __str__(self):
        return f"{self.nombre} {self.anio}"


class ModalidadPostulacion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "modalidad de postulación"
        verbose_name_plural = "modalidades de postulación"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class ProgramaEstudio(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    codigo = models.CharField(max_length=20, unique=True)
    vacantes = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "programa de estudio"
        verbose_name_plural = "programas de estudio"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre