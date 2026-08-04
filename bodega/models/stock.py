from django.db import models

from bodega.models.bodega import Bodega
from bodega.models.producto import Producto
from core.standard.models import StandardModel


class Stock(StandardModel):
    STATUS_CHOICES = [
        ('OK', 'OK'),
        ('REPOSICIÓN', 'REPOSICIÓN'),
        ('SOBRESTOCK', 'SOBRESTOCK')
    ]

    bodega = models.ForeignKey(
        Bodega,
        on_delete=models.CASCADE,
        related_name="inventario"
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="inventarios"
    )

    status_stock = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='OK',
        null=True,
        blank=True
    )

    stock_actual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    stock_minimo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    stock_maximo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    ubicacion = models.CharField(
        max_length=150,
        blank=True
    )

    class Meta:
        unique_together = ("bodega", "producto")
        ordering = ["producto__nombre"]

    def __str__(self):
        return f"{self.producto} - {self.bodega}"
