from django.db import models

from core.standard.models import StandardModelEstablishment


class TipoMovimiento(StandardModelEstablishment):
    # Ingreso
    # Asignación
    # Préstamo
    # Devolución
    # Cambio de Oficina
    # Cambio de Responsable
    # Cambio IP
    # Reparación
    # Baja
    # Inventario
    # Traslado

    nombre = models.CharField(
        max_length=100,
    )

    color = models.CharField(
        max_length=20,
        blank=True
    )

    icono = models.CharField(
        max_length=50,
        blank=True
    )

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
