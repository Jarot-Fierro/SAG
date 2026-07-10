from django.db import models

from core.standard.models import StandardModel


class Direccion(StandardModel):
    nombre = models.CharField(max_length=150,unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = "Dirección"
        verbose_name_plural = "Direcciones"

    def __str__(self):
        return self.nombre