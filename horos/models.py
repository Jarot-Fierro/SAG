from django.db import models

from config import settings
from core.standard.models import StandardModel


class PerfilHoros(StandardModel):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    acceso = models.ManyToManyField('Acceso', blank=True)


class Acceso(StandardModel):
    nombre = models.CharField(max_length=100)
    url = models.URLField()
    icono = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Acceso'
        verbose_name_plural = 'Accesos'
        ordering = ['-id']

    def __str__(self):
        return self.nombre
