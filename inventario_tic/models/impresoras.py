from django.db import models

from core.standard.models import StandardModelEstablishment


class Impresora(StandardModelEstablishment):
    numero_serie = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Número de Serie',
    )
    hh = models.CharField(
        max_length=150,
        verbose_name='HH',
    )
    marca = models.ForeignKey(
        'inventario_tic.Marca',
        on_delete=models.PROTECT,
        related_name='impresoras',
        verbose_name='Marca',
    )
    modelo = models.ForeignKey(
        'inventario_tic.Modelo',
        on_delete=models.PROTECT,
        related_name='impresoras',
        verbose_name='Modelo',
    )
    imprime_color = models.BooleanField(
        default=False,
        verbose_name='¿Imprime a Color?'
    )
    tiene_ethernet = models.BooleanField(
        default=False,
        verbose_name='¿Tiene Ethernet?'
    )
    tiene_wifi = models.BooleanField(
        default=False,
        verbose_name='¿Tiene Wi-Fi?'
    )
    toner = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Modelo de Consumible',
        help_text='Referencia del tóner, cartucho o tinta compatible.',
    )
    departamento = models.ForeignKey(
        'core.UnidadOrganizacional',
        on_delete=models.PROTECT,
        related_name='impresoras',
        verbose_name='Departamento Asignado',
    )
    observacion = models.TextField(
        blank=True,
        verbose_name='Observación'
    )

    UPPERCASE_FIELDS = ['numero_serie', 'consumible']

    class Meta:
        verbose_name = 'Impresora'
        verbose_name_plural = 'Impresoras'
        ordering = ['numero_serie']

    def __str__(self):
        return f'{self.numero_serie} - {self.marca} {self.modelo}'
