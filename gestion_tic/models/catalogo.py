from django.db import models

from core.models import Establecimiento, Departamento
from core.standard.models import StandardModel


class Marca(StandardModel):
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la Marca')

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'

    def __str__(self):
        return self.nombre


class Categoria(StandardModel):
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la Categoría')

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombre


class SubCategoria(StandardModel):
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la Subcategoría')
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        verbose_name='Categoría'
    )
    ver_mantencion = models.BooleanField(default=False)
    ver_informatica = models.BooleanField(default=False)

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Subcategoría'
        verbose_name_plural = 'Subcategorías'

    def __str__(self):
        return f"{self.categoria} - {self.nombre}"


class Modelo(StandardModel):
    nombre = models.CharField(max_length=100, verbose_name='Nombre del Modelo')

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Modelo'
        verbose_name_plural = 'Modelos'

    def __str__(self):
        return self.nombre


class Propietario(StandardModel):
    nombre = models.CharField(max_length=100, verbose_name='Nombre del Propietario')

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Propietario de Dispositivo'
        verbose_name_plural = 'Propietarios de Dispositivo'

    def __str__(self):
        return self.nombre


class LicenciaOs(StandardModel):
    nombre = models.CharField(
        max_length=100, verbose_name="Nombre de la Licencia de SO"
    )

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = "Licencia de Sistema Operativo"
        verbose_name_plural = "Licencias de Sistema Operativo"

    def __str__(self):
        return self.nombre


class MicrosoftOffice(StandardModel):
    nombre = models.CharField(
        max_length=100, verbose_name="Nombre de la Licencia de Microsoft Office"
    )

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = "Licencia de Microsoft Office"
        verbose_name_plural = "Licencias de Microsoft Office"

    def __str__(self):
        return self.nombre


class SistemaOperativo(StandardModel):
    nombre = models.CharField(
        max_length=100, verbose_name="Nombre del Sistema Operativo"
    )

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = "Sistema Operativo"
        verbose_name_plural = "Sistemas Operativos"

    def __str__(self):
        return self.nombre


class TipoCelular(StandardModel):
    nombre = models.CharField(
        max_length=100, verbose_name="Nombre del tipo plan"
    )

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = "Tipo Celular"
        verbose_name_plural = "Tipos Celular"

    def __str__(self):
        return self.nombre


class TipoComputador(StandardModel):
    nombre = models.CharField(
        max_length=100, verbose_name="Nombre del tipo computador"
    )

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = "Tipo Computador"
        verbose_name_plural = "Tipos Computador"

    def __str__(self):
        return self.nombre


class TipoImpresora(StandardModel):
    nombre = models.CharField(
        max_length=100, verbose_name="Nombre del tipo impresora"
    )

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = "Tipo Impresora"
        verbose_name_plural = "Tipos Impresoras"

    def __str__(self):
        return self.nombre


class Toner(StandardModel):
    nombre = models.CharField(max_length=100)

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Tinta'
        verbose_name_plural = 'Tintas'

    def __str__(self):
        return self.nombre


class JefeTic(StandardModel):
    nombre = models.CharField(max_length=100)
    posicion = models.CharField(max_length=100, null=True, blank=True)

    UPPERCASE_FIELDS = ['nombre', 'posicion']

    class Meta:
        verbose_name = 'JefeTic'
        verbose_name_plural = 'JefesTic'

    def __str__(self):
        return self.nombre


class Contrato(StandardModel):
    nombre = models.CharField(max_length=100)

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'

    def __str__(self):
        return self.nombre


class PuestoTrabajo(StandardModel):
    nombre = models.CharField(max_length=100)

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Puesto de Trabajo'
        verbose_name_plural = 'Puesto de Trabajo'

    def __str__(self):
        return self.nombre


class Ips(StandardModel):
    ip = models.GenericIPAddressField(
        unique=True,
        protocol='IPv4',
        verbose_name='Dirección IP'
    )
    asignado = models.BooleanField(default=False)
    establecimiento = models.ForeignKey(
        Establecimiento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ips',
        verbose_name='Establecimiento'
    )
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ips',
        verbose_name='Departamento'
    )
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
