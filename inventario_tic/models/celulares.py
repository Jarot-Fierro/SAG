from django.core.validators import RegexValidator
from django.db import models

from core.standard.models import StandardModelEstablishment


class Celular(StandardModelEstablishment):
    imei = models.CharField(
        max_length=15,
        unique=True,
        validators=[RegexValidator(
            regex=r'\A[0-9]{15}\Z',
            message='El IMEI debe contener exactamente 15 dígitos.',
        )],
        verbose_name='IMEI Principal',
    )
    numero_telefono = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Número de Teléfono',
        help_text='Incluir código de país, por ejemplo: +56912345678.',
    )
    marca = models.ForeignKey(
        'inventario_tic.Marca',
        on_delete=models.PROTECT,
        related_name='celulares',
        verbose_name='Marca',
        blank=True,
        null=True,
    )
    modelo = models.ForeignKey(
        'inventario_tic.Modelo',
        on_delete=models.PROTECT,
        related_name='celulares',
        verbose_name='Modelo',
        blank=True,
        null=True,
    )
    propietario = models.ForeignKey(
        'inventario_tic.Propietario',
        on_delete=models.PROTECT,
        related_name='propietarios',
        verbose_name='Propietario',
        blank=True,
        null=True,
    )
    minsal = models.BooleanField(
        default=False,
        verbose_name='Minsal',
    )
    pin = models.CharField(
        max_length=20,
        verbose_name='PIN',
        blank=True,
        null=True,
    )
    puk = models.CharField(
        max_length=20,
        verbose_name='PIN',
        blank=True,
        null=True,
    )
    numero_chip = models.CharField(
        max_length=100,
        verbose_name='Número de Chip',
        blank=True,
        null=True,
    )
    minutos = models.CharField(
        max_length=20,
        verbose_name='Minutos',
        blank=True,
        null=True,
    )
    establecimiento_mantenedor = models.ForeignKey(
        'inventario_tic.Establecimiento',
        on_delete=models.PROTECT,
        related_name='celulares',
        verbose_name='Establecimiento',
        blank=True,
        null=True,
    )
    jefe_entrega = models.ForeignKey(
        'inventario_tic.JefeTic',
        on_delete=models.PROTECT,
        related_name='celulares',
        verbose_name='Jefe de Entrega',
        blank=True,
        null=True,
    )
    responsable = models.ForeignKey(
        'inventario_tic.FuncionarioInventario', on_delete=models.PROTECT,
        related_name='celulares', verbose_name='Responsable', blank=True, null=True,
    )
    asignado = models.BooleanField(
        default=False,
        verbose_name='Asignado',
    )
    observacion = models.TextField(
        blank=True,
        verbose_name='Observación'
    )

    class Meta:
        verbose_name = 'Celular'
        verbose_name_plural = 'Celulares'

    def __str__(self):
        return f'{self.imei} - {self.marca} {self.modelo}'
