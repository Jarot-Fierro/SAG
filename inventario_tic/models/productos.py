from django.db import models

from core.standard.models import StandardModelEstablishment


class Producto(StandardModelEstablishment):
    nombre = models.CharField(
        max_length=150,
        verbose_name='Nombre del Producto'
    )
    tipo_producto = models.ForeignKey(
        'inventario_tic.TipoProducto',
        on_delete=models.PROTECT,
        related_name='productos',
        verbose_name='Tipo de Producto',
    )
    marca = models.ForeignKey(
        'inventario_tic.Marca',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='productos',
        verbose_name='Marca',
    )
    modelo = models.ForeignKey(
        'inventario_tic.Modelo',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='productos',
        verbose_name='Modelo',
    )
    stock_total = models.PositiveIntegerField(
        default=0,
        verbose_name='Stock Total',
    )
    stock_disponible = models.PositiveIntegerField(
        default=0,
        verbose_name='Stock Disponible',
        help_text='Cantidad de unidades disponibles de este producto.',
    )
    stock_minimo = models.PositiveIntegerField(
        default=0,
        verbose_name='Stock Mínimo'
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Ejemplo: conexión USB, capacidad de 64 GB o disco SSD de 1 TB.',
    )

    TITLE_CASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    @property
    def stock_bajo(self):
        return self.stock_disponible <= self.stock_minimo

    def __str__(self):
        return self.nombre
