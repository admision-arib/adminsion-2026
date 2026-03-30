import os
from celery import Celery

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "tu_proyecto.settings"
)

app = Celery("tu_proyecto")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()