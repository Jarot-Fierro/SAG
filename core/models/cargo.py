from django.db import models

from core.standard.models import StandardModel


class Cargo(StandardModel):
    nombre = models.CharField(max_length=150,unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"

    def __str__(self):
        return self.nombre