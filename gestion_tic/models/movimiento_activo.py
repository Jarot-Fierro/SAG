from django.conf import settings
from django.db import models

from core.models.funcionario import Funcionario
from core.models.unidad_organizacional import UnidadOrganizacional
from core.standard.models import StandardModelEstablishment
from . import JefeTic
from .activo import Activo
from .catalogo import Ips
from .tipo_movimiento import TipoMovimiento


# TipoActivo
#     │
#     ├────────────── CampoTipoActivo
#     │                     │
#     │                     └──────── OpcionCampoTipoActivo
#     │
#     │
#     ▼
# Activo
#     │
#     ├────────────── ActivoCaracteristica
#     │
#     └────────────── MovimientoActivo
#                            │
#                            ├──────── TipoMovimiento
#                            ├──────── Funcionario
#                            ├──────── UnidadOrganizacional
#                            ├──────── IP
#                            └──────── MovimientoActivoAccesorio


class MovimientoActivo(StandardModelEstablishment):
    activo = models.ForeignKey(
        Activo,
        on_delete=models.PROTECT,
        related_name="movimientos"
    )

    tipo_movimiento = models.ForeignKey(
        TipoMovimiento,
        on_delete=models.PROTECT
    )

    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    recepcionado = models.BooleanField(
        default=False,
        verbose_name="Recepcionado"
    )
    fecha_recepcion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Recepción"
    )
    recepcionado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_recepcionados",
        verbose_name="Recepcionado Por"
    )
    nombre_completo = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    departamento = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    unidad_organizacional = models.ForeignKey(
        UnidadOrganizacional,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    jefe_firmante = models.ForeignKey(
        JefeTic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    ip = models.ForeignKey(
        Ips,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    observacion = models.TextField(
        blank=True
    )

    snapshot_acta = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Copia Histórica del Acta"
    )

    class Meta:
        ordering = ["-created_at", "-id"]

    def generar_snapshot_acta(self):
        caracteristicas_list = []
        if self.activo:
            for carac in self.activo.caracteristicas.select_related('campo').all().order_by('campo__orden',
                                                                                            'campo__nombre'):
                caracteristicas_list.append({
                    'campo': carac.campo.nombre,
                    'valor': carac.valor
                })

        accesorios_list = []
        for acc in self.accesorios.all().order_by('id'):
            accesorios_list.append({
                'nombre': acc.nombre or (acc.accesorio.nombre if acc.accesorio else ''),
                'cantidad': acc.cantidad,
                'observacion': acc.observacion or ''
            })

        return {
            'activo': {
                'codigo_barra': self.activo.codigo_barra if self.activo else '',
                'tipo': self.activo.tipo.nombre if (self.activo and self.activo.tipo) else '',
                'marca': self.activo.marca.nombre if (self.activo and self.activo.marca) else '',
                'modelo': self.activo.modelo.nombre if (self.activo and self.activo.modelo) else '',
                'serie': self.activo.serie if self.activo else '',
                'observacion': self.activo.observacion if self.activo else '',
                'establecimiento': self.activo.establecimiento.nombre if (
                            self.activo and self.activo.establecimiento) else '',
                'caracteristicas': caracteristicas_list,
            },
            'ip': self.ip.ip if self.ip else None,
            'tipo_movimiento': self.tipo_movimiento.nombre if self.tipo_movimiento else '',
            'observacion': self.observacion or '',
            'nombre_completo': self.nombre_completo or (str(self.funcionario) if self.funcionario else ''),
            'departamento': self.departamento or (self.unidad_organizacional.nombre if self.unidad_organizacional else (
                self.funcionario.unidad_organizacional.nombre if self.funcionario and self.funcionario.unidad_organizacional else '')),
            'jefe_firmante': {
                'nombre': self.jefe_firmante.nombre if self.jefe_firmante else '',
                'posicion': self.jefe_firmante.posicion if self.jefe_firmante else '',
            } if self.jefe_firmante else None,
            'accesorios': accesorios_list,
            'fecha_movimiento': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else '',
            'fecha_recepcion': self.fecha_recepcion.strftime('%d/%m/%Y %H:%M') if self.fecha_recepcion else '',
        }
