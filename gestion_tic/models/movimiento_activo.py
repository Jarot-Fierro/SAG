from django.db import models

from core.models.funcionario import Funcionario
from core.models.unidad_organizacional import UnidadOrganizacional
from core.standard.models import StandardModelEstablishment
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
#                            └──────── IP


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

    unidad_organizacional = models.ForeignKey(
        UnidadOrganizacional,
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

    class Meta:
        ordering = ["-created_at"]
