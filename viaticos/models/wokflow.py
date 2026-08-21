from django.conf import settings
from django.db import models

from core.standard.models import StandardModel


class AprobacionCometido(StandardModel):
    """
    Bitácora formal e inmutable de revisiones, autorizaciones, subrogancias y firmas.
    Soporta firma digital simple y Firma Electrónica Avanzada (FEA).
    """
    ETAPA_CHOICES = [
        ('JEFE_DIRECTO', 'Aprobación Jefatura Directa'),
        ('SERVICIOS_GENERALES', 'Revisión y Asignación de SSGG'),
        ('RRHH_CONTROL', 'Control Normativo y Reloj Control (RRHH)'),
        ('DIRECCION_FIRMA', 'Firma Resolución (Director / Delegado)'),
        ('FINANZAS_PAGO', 'Autorización de Pago (Finanzas)'),
    ]

    ESTADO_ACCION_CHOICES = [
        ('APROBADO', 'Aprobado / Firmado'),
        ('RECHAZADO', 'Rechazado'),
        ('DEVUELTO', 'Devuelto con Observaciones'),
        ('SUBROGADO', 'Aprobado en Subrogancia'),
    ]

    solicitud = models.ForeignKey('viaticos.SolicitudCometidoViatico', on_delete=models.CASCADE,
                                  related_name="historial_aprobaciones", verbose_name="Solicitud")
    etapa = models.CharField(max_length=30, choices=ETAPA_CHOICES, verbose_name="Etapa del Flujo")
    accion = models.CharField(max_length=20, choices=ESTADO_ACCION_CHOICES, verbose_name="Acción Realizada")

    usuario_firmante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                         related_name="firmas_cometidos", verbose_name="Usuario Firmante")
    en_calidad_de = models.CharField(max_length=150, verbose_name="Cargo / Calidad (Titular / Subrogante)")
    es_subrogante = models.BooleanField(default=False, verbose_name="¿Firma como Subrogante?")

    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones / Motivo de Rechazo")
    fecha_hora_accion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora de la Acción")

    # Firma Electrónica
    firmado_con_fea = models.BooleanField(default=False, verbose_name="¿Firmado con FEA?")
    hash_firma_digital = models.CharField(max_length=255, blank=True, null=True,
                                          verbose_name="Hash / Certificado Firma")
    ip_registro = models.GenericIPAddressField(blank=True, null=True, verbose_name="IP de Firma")

    class Meta:
        verbose_name = "Aprobación / Firma de Cometido"
        verbose_name_plural = "Aprobaciones y Firmas de Cometidos"
        ordering = ["fecha_hora_accion"]

    def __str__(self):
        return f"[{self.get_etapa_display()}] {self.usuario_firmante} -> {self.get_accion_display()} ({self.fecha_hora_accion.strftime('%d/%m/%Y %H:%M')})"
