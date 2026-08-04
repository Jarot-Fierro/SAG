from django.db import models

from bodega.models.mantenedores import CategoriaProducto, Marca, UnidadMedida
from core.standard.models import StandardModel


class Producto(StandardModel):
    codigo = models.CharField(max_length=50, unique=True, blank=True, null=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)

    categoria = models.ForeignKey(
        CategoriaProducto,
        on_delete=models.PROTECT
    )

    marca = models.ForeignKey(
        Marca,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    unidad_medida = models.ForeignKey(
        UnidadMedida,
        on_delete=models.PROTECT
    )

    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
