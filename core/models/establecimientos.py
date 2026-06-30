from django.db import models

from core.standard.models import StandardModel


class Establecimiento(StandardModel):
    nombre = models.CharField(max_length=200)
    alias = models.CharField(max_length=20, unique=True, null=True, blank=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    direccion = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Establecimiento'
        verbose_name_plural = 'Establecimientos'
        ordering = ['nombre']
