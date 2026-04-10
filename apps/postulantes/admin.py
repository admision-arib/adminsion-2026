from django.contrib import admin
from apps.postulantes.models import Postulante
from apps.postulantes.models import Inscripcion
# Register your models here.
admin.site.register(Postulante)
admin.site.register(Inscripcion)
