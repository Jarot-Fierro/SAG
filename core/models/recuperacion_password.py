from django.conf import settings
from django.db import models
from django.utils import timezone


class RecuperacionPassword(models.Model):
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('UTILIZADO', 'Utilizado'),
        ('EXPIRADO', 'Expirado'),
        ('CANCELADO', 'Cancelado'),
    )

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='recuperaciones_password')
    establecimiento = models.ForeignKey('core.Establecimiento', on_delete=models.CASCADE)
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    utilizado = models.BooleanField(default=False)
    fecha_utilizacion = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE', db_index=True)

    # Información de la solicitud
    ip_solicitud = models.GenericIPAddressField(null=True, blank=True)
    user_agent_solicitud = models.TextField(null=True, blank=True)
    navegador_solicitud = models.CharField(max_length=100, null=True, blank=True)
    version_navegador_solicitud = models.CharField(max_length=50, null=True, blank=True)
    sistema_operativo_solicitud = models.CharField(max_length=100, null=True, blank=True)
    dispositivo_solicitud = models.CharField(max_length=100, null=True, blank=True)
    es_pc_solicitud = models.BooleanField(default=False)
    es_tablet_solicitud = models.BooleanField(default=False)
    es_movil_solicitud = models.BooleanField(default=False)
    es_bot_solicitud = models.BooleanField(default=False)

    # Información de utilización
    ip_utilizacion = models.GenericIPAddressField(null=True, blank=True)
    user_agent_utilizacion = models.TextField(null=True, blank=True)
    navegador_utilizacion = models.CharField(max_length=100, null=True, blank=True)
    version_navegador_utilizacion = models.CharField(max_length=50, null=True, blank=True)
    sistema_operativo_utilizacion = models.CharField(max_length=100, null=True, blank=True)
    dispositivo_utilizacion = models.CharField(max_length=100, null=True, blank=True)
    es_pc_utilizacion = models.BooleanField(default=False)
    es_tablet_utilizacion = models.BooleanField(default=False)
    es_movil_utilizacion = models.BooleanField(default=False)
    es_bot_utilizacion = models.BooleanField(default=False)

    # Geolocalización (preparado para GeoIP2)
    pais = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    ciudad = models.CharField(max_length=100, null=True, blank=True)

    # Auditoría
    observacion = models.TextField(null=True, blank=True)
    solicitud_exitosa = models.BooleanField(default=True)

    def is_expired(self):
        return timezone.now() > self.fecha_expiracion

    def __str__(self):
        return f"Recuperación {self.usuario.username} - {self.estado}"

    class Meta:
        verbose_name = 'Recuperación de Contraseña'
        verbose_name_plural = 'Recuperaciones de Contraseña'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['token_hash']),
            models.Index(fields=['estado']),
        ]
