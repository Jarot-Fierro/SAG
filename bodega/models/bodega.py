from django.db import models

from bodega.models.mantenedores import CategoriaProducto
from core.standard.models import StandardModelEstablishment


class Bodega(StandardModelEstablishment):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)

    categorias = models.ManyToManyField(
        CategoriaProducto,
        blank=True,
        related_name="bodegas"
    )

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
