from django.db import models

from core.standard.models import StandardModel


class Ubicacion(StandardModel):
    nombre = models.CharField(max_length=150, unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"

    def __str__(self):
        return self.nombre
