from django.db import models

from core.standard.models import StandardModelEstablishment
from .catalogo import Marca, Modelo, Contrato
from .tipo_activo import TipoActivo


class Activo(StandardModelEstablishment):
    codigo_barra = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Código de Barras"
    )

    tipo = models.ForeignKey(
        TipoActivo,
        on_delete=models.PROTECT
    )

    marca = models.ForeignKey(
        Marca,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    modelo = models.ForeignKey(
        Modelo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    serie = models.CharField(
        max_length=150,
        blank=True
    )
    contrato = models.ForeignKey(Contrato, on_delete=models.SET_NULL, null=True, blank=True)

    observacion = models.TextField(
        blank=True
    )

    de_baja = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ["codigo_barra"]

    def __str__(self):
        return f"{self.codigo_barra}"
