from colorfield.fields import ColorField
from django.db import models

from core.standard.models import StandardModel


class Modulo(StandardModel):
    COLOR_CHOICES = [
        ("#006FB3", "Primary (Azul)"),
        ("#7F8F99", "Secondary (Gris)"),
        ("#3fa1ad", "Success (Verde)"),
        ("#876bbe", "Info (Morado)"),
        ("#FFA11B", "Warning (Naranja)"),
    ]

    nombre = models.CharField(max_length=100)
    icono = models.TextField(blank=True)
    codigo = models.CharField(
        max_length=50,
        unique=True
    )
    url = models.CharField(max_length=200, blank=True)
    consulta = models.CharField(max_length=200, blank=True)
    color = ColorField(default='#006FB3', samples=COLOR_CHOICES)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Modulo'
        verbose_name_plural = 'Modulos'
        ordering = ['nombre']
