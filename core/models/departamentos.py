from django.db import models

from core.standard.models import StandardModelEstablishment


class Departamento(StandardModelEstablishment):
    nombre = models.CharField(max_length=100)

    UPPERCASE_FIELDS = ['nombre', ]

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'
        ordering = ['nombre']
