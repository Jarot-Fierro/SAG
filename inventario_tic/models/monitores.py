from django.core.validators import MinValueValidator
from django.db import models, router, transaction

from core.standard.models import StandardModelEstablishment


class Monitor(StandardModelEstablishment):
    codigo_inventario = models.CharField(
        max_length=100, unique=True, null=True, blank=True, editable=False,
        verbose_name='Código de Inventario',
    )
    numero_serie = models.CharField(
        max_length=150, unique=True, verbose_name='Número de Serie',
    )
    marca = models.ForeignKey(
        'inventario_tic.Marca', on_delete=models.PROTECT,
        related_name='monitores', verbose_name='Marca',
    )
    modelo = models.ForeignKey(
        'inventario_tic.Modelo', on_delete=models.PROTECT,
        related_name='monitores', verbose_name='Modelo',
    )
    pulgadas = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(1)], verbose_name='Tamaño en Pulgadas',
    )
    resolucion = models.CharField(
        max_length=50, blank=True, verbose_name='Resolución',
        help_text='Ejemplo: 1920 x 1080.',
    )
    frecuencia_hz = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)],
        verbose_name='Frecuencia de Actualización (Hz)',
    )
    tiene_hdmi = models.BooleanField(default=False, verbose_name='¿Tiene HDMI?')
    tiene_displayport = models.BooleanField(default=False, verbose_name='¿Tiene DisplayPort?')
    tiene_vga = models.BooleanField(default=False, verbose_name='¿Tiene VGA?')
    tiene_dvi = models.BooleanField(default=False, verbose_name='¿Tiene DVI?')
    tiene_usb_c = models.BooleanField(default=False, verbose_name='¿Tiene USB-C?')
    observacion = models.TextField(blank=True, verbose_name='Observación')

    establecimiento_mantenedor = models.ForeignKey(
        'inventario_tic.Establecimiento', on_delete=models.PROTECT,
        related_name='monitores', verbose_name='Establecimiento Destino', blank=True, null=True,
    )
    responsable = models.CharField(max_length=255, verbose_name='Responsable', blank=True, null=True)
    jefe_entrega = models.ForeignKey(
        'inventario_tic.JefeTic', on_delete=models.PROTECT,
        related_name='monitores', verbose_name='Jefe de Entrega', blank=True, null=True,
    )
    asignado = models.BooleanField(default=False, verbose_name='Asignado')

    UPPERCASE_FIELDS = ['numero_serie']

    class Meta:
        verbose_name = 'Monitor'
        verbose_name_plural = 'Monitores'
        ordering = ['codigo_inventario']

    def __str__(self):
        return f'{self.codigo_inventario} - {self.marca} {self.modelo}'

    def save(self, *args, **kwargs):
        using = kwargs.get('using') or router.db_for_write(type(self), instance=self)
        kwargs['using'] = using
        with transaction.atomic(using=using):
            if self.pk is None:
                self.codigo_inventario = None
                super().save(*args, **kwargs)
                self.codigo_inventario = f'SSA-MON-{self.pk}'
                super().save(using=using, update_fields=['codigo_inventario'])
            else:
                self.codigo_inventario = f'SSA-MON-{self.pk}'
                if kwargs.get('update_fields') is not None:
                    kwargs['update_fields'] = set(kwargs['update_fields']) | {'codigo_inventario'}
                super().save(*args, **kwargs)
