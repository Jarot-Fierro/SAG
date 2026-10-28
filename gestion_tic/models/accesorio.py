from django.db import models

from core.standard.models import StandardModelEstablishment


class Accesorio(StandardModelEstablishment):
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre del Accesorio"
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción"
    )
    incluido_en_estacion_completa = models.BooleanField(
        default=False,
        verbose_name="¿Incluido en Estación Completa?",
        help_text="Define si este accesorio forma parte del paquete de estación completa."
    )
    cantidad_estacion_completa = models.PositiveIntegerField(
        default=1,
        verbose_name="Cantidad en Estación Completa",
        help_text="Cantidad por defecto de este accesorio en una estación completa."
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Accesorio"
        verbose_name_plural = "Accesorios"

    def __str__(self):
        return self.nombre


class MovimientoActivoAccesorio(StandardModelEstablishment):
    movimiento = models.ForeignKey(
        'gestion_tic.MovimientoActivo',
        on_delete=models.CASCADE,
        related_name="accesorios"
    )
    accesorio = models.ForeignKey(
        Accesorio,
        on_delete=models.PROTECT,
        related_name="movimientos_asociados"
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre del Accesorio (Histórico)",
        help_text="Conserva el nombre del accesorio al momento de la entrega para trazabilidad histórica."
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        verbose_name="Cantidad"
    )
    observacion = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Observación o Estado"
    )

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=['movimiento', 'accesorio'],
                name='unique_accesorio_por_movimiento'
            )
        ]
        verbose_name = "Accesorio de Movimiento"
        verbose_name_plural = "Accesorios de Movimiento"

    def save(self, *args, **kwargs):
        if not self.nombre and self.accesorio:
            self.nombre = self.accesorio.nombre
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad}x {self.nombre or (self.accesorio.nombre if self.accesorio else '')}"
