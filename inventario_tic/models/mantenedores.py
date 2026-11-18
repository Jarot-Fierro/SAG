from django.db import models
from django.utils import timezone

from core.standard.models import StandardModelEstablishment


class TipoProducto(StandardModelEstablishment):
    nombre = models.CharField(max_length=100, verbose_name='Nombre del Tipo de Producto')

    TITLE_CASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Tipo de Producto'
        verbose_name_plural = 'Tipos de Producto'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Marca(StandardModelEstablishment):
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la Marca')

    TITLE_CASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Establecimiento(StandardModelEstablishment):
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la Marca')

    TITLE_CASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Establecimiento'
        verbose_name_plural = 'Establecimientos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Modelo(StandardModelEstablishment):
    nombre = models.CharField(max_length=100, verbose_name='Nombre del Modelo')
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, verbose_name='Marca')

    TITLE_CASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Modelo'
        verbose_name_plural = 'Modelos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Propietario(StandardModelEstablishment):
    nombre = models.CharField(max_length=100, verbose_name='Nombre del Propietario')

    TITLE_CASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Propietario de Dispositivo'
        verbose_name_plural = 'Propietarios de Dispositivo'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class JefeTic(StandardModelEstablishment):
    nombre = models.CharField(max_length=100)
    posicion = models.CharField(max_length=100, null=True, blank=True)

    TITLE_CASE_FIELDS = ['nombre', 'posicion']

    class Meta:
        verbose_name = 'JefeTic'
        verbose_name_plural = 'JefesTic'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Contrato(StandardModelEstablishment):
    nombre = models.CharField(max_length=100)
    file = models.FileField(
        upload_to='gestion_tic/documentos/contratos/%Y',
        null=True,
        blank=True
    )
    fecha_inicio = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de inicio',
    )
    fecha_vencimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de vencimiento',
    )
    dias_aviso = models.PositiveIntegerField(
        default=30,
        verbose_name='Días de anticipación del aviso',
    )
    notificar_vencimiento = models.BooleanField(
        default=True,
        verbose_name='Notificar vencimiento',
    )

    TITLE_CASE_FIELDS = ['nombre']

    @property
    def proximo_a_vencer(self):
        if not self.fecha_vencimiento:
            return False

        dias_restantes = (
                self.fecha_vencimiento - timezone.localdate()
        ).days

        return 0 <= dias_restantes <= self.dias_aviso

    class Meta:
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Ips(StandardModelEstablishment):
    ip = models.GenericIPAddressField(
        unique=True,
        protocol='IPv4',
        verbose_name='Dirección IP'
    )
    mascara = models.GenericIPAddressField(
        protocol='IPv4',
        verbose_name='Máscara',
        null=True,
        blank=True
    )
    gateway = models.GenericIPAddressField(
        protocol='IPv4',
        verbose_name='Gateway',
        null=True,
        blank=True
    )
    vlan = models.CharField(
        max_length=50,
        verbose_name='VLAN',
        null=True,
        blank=True
    )
    asignado = models.BooleanField(default=False)
    observacion = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observación'
    )

    class Meta:
        verbose_name = 'Dirección IP'
        verbose_name_plural = 'Direcciones IP'
        ordering = ['ip']

    def __str__(self):
        return f'{self.ip}'


class FuncionarioInventario(StandardModelEstablishment):
    nombre = models.CharField(max_length=255, verbose_name='Nombre completo')

    class Meta:
        verbose_name = 'Funcionario de inventario'
        verbose_name_plural = 'Funcionarios de inventario'
        ordering = ['nombre', 'pk']

    def __str__(self):
        return self.nombre
