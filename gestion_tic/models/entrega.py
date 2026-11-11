from django.conf import settings
from django.db import models
from core.standard.models import StandardModelEstablishment


class EntregaActivos(StandardModelEstablishment):
    class Estado(models.TextChoices):
        BORRADOR = 'borrador', 'Borrador'
        PENDIENTE = 'pendiente', 'Pendiente de recepción'
        RECEPCIONADA = 'recepcionada', 'Recepcionada'

    funcionario = models.ForeignKey('core.Funcionario', on_delete=models.PROTECT)
    tipo_movimiento = models.ForeignKey('gestion_tic.TipoMovimiento', on_delete=models.PROTECT)
    jefe_firmante = models.ForeignKey('gestion_tic.JefeTic', on_delete=models.PROTECT)
    observacion = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.BORRADOR)
    fecha_recepcion = models.DateTimeField(null=True, blank=True)
    recepcionado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                         null=True, blank=True, related_name='entregas_recepcionadas')
    snapshot_acta = models.JSONField(null=True, blank=True)


class DetalleEntrega(models.Model):
    entrega = models.ForeignKey(EntregaActivos, on_delete=models.CASCADE, related_name='detalles')
    activo = models.ForeignKey('gestion_tic.Activo', on_delete=models.PROTECT)
    ip = models.ForeignKey('gestion_tic.Ips', on_delete=models.PROTECT, null=True, blank=True)
    observacion = models.TextField(blank=True)
    accesorios = models.JSONField(default=list, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['entrega', 'activo'], name='entrega_activo_unico')]
        ordering = ['pk']
