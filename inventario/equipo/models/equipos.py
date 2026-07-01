from django.core.exceptions import ValidationError
from django.db import models

from core.models import Departamento, Establecimiento, User
from core.standard.models import StandardModel
from inventario.catalogo.models import (Marca, Modelo, TipoComputador, TipoImpresora, SistemaOperativo, MicrosoftOffice,
                                        Toner,
                                        Propietario, JefeTic, Contrato, Ips)


class Equipo(StandardModel):
    TIPO_EQUIPO = (
        ('PC', 'Computador'),
        ('IMP', 'Impresora'),
        ('NB', 'Notebook'),
        ('ROU', 'Router'),
        ('SW', 'Switch'),
        ('SCAN', 'Scanner'),
        ('OTRO', 'Otro'),
    )

    # =========================
    # IDENTIFICACIÓN GENERAL
    # =========================
    tipo_equipo = models.CharField(max_length=10, choices=TIPO_EQUIPO)
    serie = models.CharField(max_length=100, unique=True)
    ip = models.OneToOneField(Ips, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipo')
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    modelo = models.ForeignKey(Modelo, on_delete=models.SET_NULL, null=True, blank=True)

    # =========================
    # UBICACIÓN / RESPONSABLE
    # =========================
    propietario = models.ForeignKey(Propietario, on_delete=models.SET_NULL, null=True, blank=True)
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True)
    establecimiento = models.ForeignKey(Establecimiento, on_delete=models.SET_NULL, null=True, blank=True)
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    jefe_entrega = models.ForeignKey(JefeTic, on_delete=models.SET_NULL, null=True, blank=True)
    contrato = models.ForeignKey(Contrato, on_delete=models.SET_NULL, null=True, blank=True)

    # =========================
    # CAMPOS PC / NOTEBOOK
    # =========================
    tipo_pc = models.ForeignKey(TipoComputador, on_delete=models.SET_NULL, null=True, blank=True)
    mac = models.CharField(max_length=30, null=True, blank=True)
    sistema_operativo = models.ForeignKey(SistemaOperativo, on_delete=models.SET_NULL, null=True, blank=True)
    microsoft_office = models.ForeignKey(MicrosoftOffice, on_delete=models.SET_NULL, null=True, blank=True)

    # PC ARMADO
    es_armado = models.BooleanField(default=False)
    ram_gb = models.CharField(max_length=50, null=True, blank=True)
    wifi = models.CharField(max_length=100, null=True, blank=True)
    procesador = models.CharField(max_length=150, null=True, blank=True)
    tarjeta_video = models.CharField(max_length=150, null=True, blank=True)
    red_lan = models.CharField(max_length=100, null=True, blank=True)

    tipo_disco = models.CharField(max_length=20, choices=[('SSD', 'SSD'), ('HDD', 'Mecánico'), ('NVME', 'NVMe')],
                                  null=True, blank=True)

    capacidad_disco_gb = models.IntegerField(null=True, blank=True)

    # =========================
    # CAMPOS IMPRESORA
    # =========================
    tipo_impresora = models.ForeignKey(TipoImpresora, on_delete=models.SET_NULL, null=True, blank=True)
    hh = models.CharField(max_length=30, null=True, blank=True)
    toner = models.ForeignKey(Toner, on_delete=models.SET_NULL, null=True, blank=True)

    # =========================
    # ESTADO GENERAL
    # =========================
    de_baja = models.BooleanField(default=False)
    motivo_baja = models.TextField(null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)

    UPPERCASE_FIELDS = [
        'serie',
        'mac',
        'hh',
        'motivo_baja',
        'observaciones'
    ]

    # =========================
    # PROPIEDADES
    # =========================

    @property
    def tiene_ip(self):
        return self.ip is not None

    @property
    def es_computador(self):
        return self.tipo_equipo == 'PC'

    @property
    def es_impresora(self):
        return self.tipo_equipo == 'IMP'

    # =========================
    # VALIDACIONES
    # =========================
    def clean(self):

        # Computador requiere campos PC
        if self.tipo_equipo == 'PC':
            if not self.tipo_pc:
                raise ValidationError("Debe seleccionar tipo computador.")

        # Impresora requiere campos impresora
        if self.tipo_equipo == 'IMP':
            if not self.tipo_impresora:
                raise ValidationError("Debe seleccionar tipo impresora.")

    # =========================
    # META
    # =========================
    class Meta:
        verbose_name = 'Equipo'
        verbose_name_plural = 'Equipos'
        ordering = ['serie']
        db_table = 'inventario_equipo_equipos'

    def __str__(self):
        return f'{self.get_tipo_equipo_display()} - {self.serie}'


class AsignacionIP(StandardModel):
    ip = models.OneToOneField(Ips, on_delete=models.CASCADE, related_name='asignacion_ip', verbose_name='Dirección IP')
    equipo = models.OneToOneField(Equipo, on_delete=models.CASCADE, related_name='asignacion_ip', verbose_name='Equipo',
                                  null=True, blank=True)
    activa = models.BooleanField(default=True, verbose_name='Asignación activa')
    observacion = models.TextField(null=True, blank=True)

    UPPERCASE_FIELDS = ['observacion']

    class Meta:
        verbose_name = 'Asignación IP'
        verbose_name_plural = 'Asignaciones IP'
        ordering = ['-updated_at']
        db_table = 'inventario_equipo_asignacionip'

    def __str__(self):
        estado = "ACTIVA" if self.activa else "LIBERADA"
        return f'{self.ip.ip} → {self.equipo} ({estado})'
