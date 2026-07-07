from django.conf import settings
from django.db import models

from core.models import Departamento, Establecimiento
from core.standard.models import StandardModel
from gestion_tic.models.catalogo import Marca, Modelo, TipoCelular, Propietario, JefeTic, Contrato


class Celular(StandardModel):
    imei = models.CharField(max_length=30)
    numero_telefono = models.CharField(max_length=15)
    minsal = models.BooleanField(default=False)
    pin = models.CharField(max_length=50, null=True, blank=True)
    puk = models.CharField(max_length=50, null=True, blank=True)
    numero_chip = models.CharField(max_length=50, null=True, blank=True)
    minutos = models.CharField(max_length=50, null=True, blank=True)

    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE, null=True, blank=True)
    tipo = models.ForeignKey(TipoCelular, on_delete=models.CASCADE, null=True, blank=True)
    asignado = models.BooleanField(default=False)
    propietario = models.ForeignKey(
        Propietario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='celular_propietario'
    )
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='celular_departamento'
    )
    jefe_entrega = models.ForeignKey(
        JefeTic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='celular_jefetic'
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='celular_responsable'
    )
    contrato = models.ForeignKey(
        Contrato,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='celular_contrato'
    )
    establecimiento = models.ForeignKey(
        Establecimiento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='celular_establecimiento'
    )
    de_baja = models.BooleanField(default=False)
    motivo_baja = models.TextField(null=True, blank=True)

    observaciones = models.TextField(null=True, blank=True)

    UPPERCASE_FIELDS = ['motivo_baja', 'observaciones']

    class Meta:
        verbose_name = 'Celular'
        verbose_name_plural = 'Celulares'

    def __str__(self):
        return self.numero_telefono
