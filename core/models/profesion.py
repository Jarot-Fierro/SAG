from django.db import models

from core.standard.models import StandardModel


class Profesion(StandardModel):
    nombre = models.CharField(max_length=100,unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = "Profesión"
        verbose_name_plural = "Profesiones"

    def __str__(self):
        return self.nombre