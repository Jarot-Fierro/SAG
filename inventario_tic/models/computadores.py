from django.core.validators import MinValueValidator
from django.db import models, transaction, router

from core.standard.models import StandardModelEstablishment


class Computador(StandardModelEstablishment):
    contrato = models.ForeignKey('inventario_tic.Contrato', on_delete=models.PROTECT,
                                 null=True, blank=True, related_name='computadores', verbose_name='Contrato')
    class Formato(models.TextChoices):
        ESCRITORIO = 'ESCRITORIO', 'Escritorio'
        NOTEBOOK = 'NOTEBOOK', 'Notebook'
        ALL_IN_ONE = 'ALL_IN_ONE', 'All in One'
        MINI_PC = 'MINI_PC', 'Mini PC'
        OTRO = 'OTRO', 'Otro'

    codigo_inventario = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        editable=False,
        verbose_name='Código de Inventario',
    )
    numero_serie = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Número de Serie',
    )
    marca = models.ForeignKey(
        'inventario_tic.Marca',
        on_delete=models.PROTECT,
        related_name='computadores',
        verbose_name='Marca',
    )
    modelo = models.ForeignKey(
        'inventario_tic.Modelo',
        on_delete=models.PROTECT,
        related_name='computadores',
        verbose_name='Modelo',
    )
    formato = models.CharField(
        max_length=20,
        choices=Formato.choices,
        verbose_name='Formato del Equipo',
    )
    procesador = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Procesador'
    )
    memoria_ram_gb = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name='Memoria RAM (GB)',
    )
    almacenamiento = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Almacenamiento',
        help_text='Ejemplo: SSD NVMe de 512 GB + HDD de 1 TB.',
    )
    tarjeta_grafica = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Tarjeta Gráfica',
    )
    observacion = models.TextField(
        blank=True,
        verbose_name='Observación'
    )

    establecimiento_mantenedor = models.ForeignKey(
        'inventario_tic.Establecimiento', on_delete=models.PROTECT,
        related_name='computadores', verbose_name='Establecimiento Destino', blank=True, null=True,
    )
    jefe_entrega = models.ForeignKey(
        'inventario_tic.JefeTic', on_delete=models.PROTECT,
        related_name='computadores', verbose_name='Jefe de Entrega', blank=True, null=True,
    )
    responsable = models.ForeignKey(
        'inventario_tic.FuncionarioInventario', on_delete=models.PROTECT,
        related_name='computadores', verbose_name='Responsable', blank=True, null=True,
    )
    asignado = models.BooleanField(default=False, verbose_name='Asignado')

    UPPERCASE_FIELDS = [
        'codigo_inventario'
    ]
    TITLE_CASE_FIELDS = [
        'procesador',
        'almacenamiento', 'tarjeta_grafica',
    ]

    class Meta:
        verbose_name = 'Computador'
        verbose_name_plural = 'Computadores'
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
                self.codigo_inventario = f'SSA-PC-{self.pk}'
                super().save(using=using, update_fields=['codigo_inventario'])
            else:
                self.codigo_inventario = f'SSA-PC-{self.pk}'
                if kwargs.get('update_fields') is not None:
                    kwargs['update_fields'] = set(kwargs['update_fields']) | {'codigo_inventario'}
                super().save(*args, **kwargs)
