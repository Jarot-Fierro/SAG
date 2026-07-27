from django.db import models

from core.standard.models import StandardModelEstablishment
from .campo_tipo_activo import CampoTipoActivo


class OpcionCampoTipoActivo(StandardModelEstablishment):
    # Láser
    # Tinta
    # Multifuncional
    # Térmica

    campo = models.ForeignKey(
        CampoTipoActivo,
        on_delete=models.CASCADE,
        related_name="opciones"
    )

    nombre = models.CharField(
        max_length=100
    )

    orden = models.PositiveIntegerField(
        default=0
    )

    class Meta:
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre
