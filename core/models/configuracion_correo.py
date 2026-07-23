from django.db import models

from core.utils.encryption import encrypt_value, decrypt_value


class ConfiguracionCorreo(models.Model):
    establecimiento = models.OneToOneField(
        'core.Establecimiento',
        on_delete=models.CASCADE,
        related_name='configuracion_correo',
        verbose_name='Establecimiento'
    )
    nombre_remitente = models.CharField(max_length=200, verbose_name='Nombre del Remitente')
    email_remitente = models.EmailField(verbose_name='Email del Remitente')
    smtp_host = models.CharField(max_length=255, verbose_name='Host SMTP')
    smtp_port = models.PositiveIntegerField(verbose_name='Puerto SMTP')
    smtp_tls = models.BooleanField(default=True, verbose_name='Usar TLS')
    smtp_ssl = models.BooleanField(default=False, verbose_name='Usar SSL')
    smtp_usuario = models.CharField(max_length=255, verbose_name='Usuario SMTP')
    _smtp_password = models.TextField(db_column='smtp_password', verbose_name='Contraseña SMTP')
    activo = models.BooleanField(default=True, verbose_name='Activo')

    @property
    def smtp_password(self):
        return decrypt_value(self._smtp_password)

    @smtp_password.setter
    def smtp_password(self, value):
        self._smtp_password = encrypt_value(value)

    def __str__(self):
        return f"Configuración correo: {self.establecimiento.nombre}"

    def save(self, *args, **kwargs):
        # Salvaguarda: si _smtp_password tiene un valor que no parece estar cifrado
        # (los tokens de Fernet comienzan por 'gAAAA'), lo ciframos.
        if self._smtp_password and not self._smtp_password.startswith('gAAAA'):
            self._smtp_password = encrypt_value(self._smtp_password)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Configuración de Correo'
        verbose_name_plural = 'Configuraciones de Correo'
