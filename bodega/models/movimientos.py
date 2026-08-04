from django.db import models

from bodega.models.stock import Stock
from config import settings
from core.standard.models import StandardModelEstablishment


class MovimientoInventario(StandardModelEstablishment):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    AJUSTE = "AJUSTE"
    TRANSFERENCIA = "TRANSFERENCIA"

    TIPO_CHOICES = [
        (ENTRADA, "Entrada"),
        (SALIDA, "Salida"),
        (AJUSTE, "Ajuste"),
        (TRANSFERENCIA, "Transferencia"),
    ]

    inventario = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name="movimientos"
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES
    )

    cantidad = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )

    observacion = models.TextField(blank=True)

    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.tipo} - {self.inventario.producto}"
