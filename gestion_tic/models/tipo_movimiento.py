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
    requiere_recepcion = models.BooleanField(
        default=False,
        verbose_name="¿Requiere Recepción Conforme?",
        help_text="Indica si este tipo de movimiento requiere confirmación de recepción conforme por el receptor."
    )
    es_asignacion = models.BooleanField(
        default=False,
        verbose_name="¿Es Asignación?",
        help_text="Indica si este tipo de movimiento representa una asignación del equipo."
    )

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
