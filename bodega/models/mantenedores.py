from django.db import models

from core.standard.models import StandardModel


class CategoriaProducto(StandardModel):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre


class Marca(StandardModel):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class UnidadMedida(StandardModel):
    nombre = models.CharField(max_length=50)
    abreviatura = models.CharField(max_length=10)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Responsable(StandardModel):
    nombre = models.CharField(max_length=255)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
