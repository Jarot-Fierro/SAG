from django.db import models

from core.standard.models import StandardModelEstablishment


class Marca(StandardModelEstablishment):
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la Marca')

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Modelo(StandardModelEstablishment):
    nombre = models.CharField(max_length=100, verbose_name='Nombre del Modelo')

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Modelo'
        verbose_name_plural = 'Modelos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Propietario(StandardModelEstablishment):
    nombre = models.CharField(max_length=100, verbose_name='Nombre del Propietario')

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Propietario de Dispositivo'
        verbose_name_plural = 'Propietarios de Dispositivo'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class LicenciaOs(StandardModelEstablishment):
    nombre = models.CharField(
        max_length=100, verbose_name="Nombre de la Licencia de SO"
    )

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = "Licencia de Sistema Operativo"
        verbose_name_plural = "Licencias de Sistema Operativo"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class MicrosoftOffice(StandardModelEstablishment):
    nombre = models.CharField(
        max_length=100, verbose_name="Nombre de la Licencia de Microsoft Office"
    )

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = "Licencia de Microsoft Office"
        verbose_name_plural = "Licencias de Microsoft Office"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class TipoCelular(StandardModelEstablishment):
    nombre = models.CharField(
        max_length=100, verbose_name="Nombre del tipo plan"
    )

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = "Tipo Celular"
        verbose_name_plural = "Tipos Celular"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class TipoComputador(StandardModelEstablishment):
    nombre = models.CharField(
        max_length=100, verbose_name="Nombre del tipo computador"
    )

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = "Tipo Computador"
        verbose_name_plural = "Tipos Computador"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class TipoImpresora(StandardModelEstablishment):
    nombre = models.CharField(
        max_length=100, verbose_name="Nombre del tipo impresora"
    )

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = "Tipo Impresora"
        verbose_name_plural = "Tipos Impresoras"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Toner(StandardModelEstablishment):
    nombre = models.CharField(max_length=100)

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Tinta'
        verbose_name_plural = 'Tintas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class JefeTic(StandardModelEstablishment):
    nombre = models.CharField(max_length=100)
    posicion = models.CharField(max_length=100, null=True, blank=True)

    UPPERCASE_FIELDS = ['nombre', 'posicion']

    class Meta:
        verbose_name = 'JefeTic'
        verbose_name_plural = 'JefesTic'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Contrato(StandardModelEstablishment):
    nombre = models.CharField(max_length=100)

    UPPERCASE_FIELDS = ['nombre']

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
    asignado = models.BooleanField(default=False)
    observacion = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observación'
    )

    UPPERCASE_FIELDS = ['observacion']

    class Meta:
        verbose_name = 'Dirección IP'
        verbose_name_plural = 'Direcciones IP'
        ordering = ['ip']

    def __str__(self):
        return f'{self.ip}'
