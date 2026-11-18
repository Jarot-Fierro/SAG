from django.core.validators import MinValueValidator, RegexValidator
from django.db import models, router, transaction

from core.standard.models import StandardModelEstablishment


class Celular(StandardModelEstablishment):
    codigo_inventario = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        editable=False,
        verbose_name='Código de Inventario',
    )
    numero_telefono = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Número de Teléfono',
        help_text='Incluir código de país, por ejemplo: +56912345678.',
    )
    imei = models.CharField(
        max_length=15,
        unique=True,
        validators=[RegexValidator(
            regex=r'\A[0-9]{15}\Z',
            message='El IMEI debe contener exactamente 15 dígitos.',
        )],
        verbose_name='IMEI Principal',
    )

    marca = models.ForeignKey(
        'inventario_tic.Marca',
        on_delete=models.PROTECT,
        related_name='celulares',
        verbose_name='Marca',
    )
    modelo = models.ForeignKey(
        'inventario_tic.Modelo',
        on_delete=models.PROTECT,
        related_name='celulares',
        verbose_name='Modelo',
    )
    memoria_ram_gb = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name='Memoria RAM (GB)',
    )
    almacenamiento_gb = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name='Almacenamiento Interno (GB)',
    )
    sistema_operativo = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Sistema Operativo',
        help_text='Ejemplo: Android 16 o iOS 26.',
    )
    dual_sim = models.BooleanField(
        default=False,
        verbose_name='¿Admite Dual SIM?'
    )
    observacion = models.TextField(
        blank=True,
        verbose_name='Observación'
    )

    UPPERCASE_FIELDS = []

    class Meta:
        verbose_name = 'Celular'
        verbose_name_plural = 'Celulares'
        ordering = ['codigo_inventario']

    def __str__(self):
        return f'{self.codigo_inventario} - {self.marca} {self.modelo}'

    def save(self, *args, **kwargs):
        using = kwargs.get('using') or router.db_for_write(type(self), instance=self)
        kwargs['using'] = using
        with transaction.atomic(using=using):
            if self.pk is None:
                # El primer guardado obtiene el ID asignado por la base de datos.
                self.codigo_inventario = None
                super().save(*args, **kwargs)
                self.codigo_inventario = f'SSA-CEL-{self.pk}'
                super().save(using=using, update_fields=['codigo_inventario'])
            else:
                self.codigo_inventario = f'SSA-CEL-{self.pk}'
                if kwargs.get('update_fields') is not None:
                    kwargs['update_fields'] = set(kwargs['update_fields']) | {'codigo_inventario'}
                super().save(*args, **kwargs)
