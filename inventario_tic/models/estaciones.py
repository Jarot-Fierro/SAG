from django.conf import settings
from django.db import models


class AsignacionEstacion(models.Model):
    """Registro inmutable de una entrega; el acta conserva los datos originales."""

    establecimiento = models.ForeignKey('core.Establecimiento', on_delete=models.PROTECT)
    destino = models.ForeignKey('inventario_tic.Establecimiento', on_delete=models.PROTECT)
    responsable = models.ForeignKey('inventario_tic.FuncionarioInventario', on_delete=models.PROTECT)
    jefe_entrega = models.ForeignKey('inventario_tic.JefeTic', on_delete=models.PROTECT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    contenido = models.JSONField()

    class Meta:
        ordering = ['-pk']
        verbose_name = 'Asignación de estación de trabajo'


class ProductoAsignadoEstacion(models.Model):
    asignacion = models.ForeignKey(AsignacionEstacion, on_delete=models.PROTECT, related_name='productos')
    producto = models.ForeignKey('inventario_tic.Producto', on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['asignacion', 'producto'], name='estacion_producto_unico'),
            models.CheckConstraint(condition=models.Q(cantidad__gte=1), name='estacion_cantidad_positiva'),
        ]
