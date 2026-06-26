from django.db import models
from django.utils import timezone

from core.standard.models import StandardModel


class PerfilSoporte(StandardModel):
    usuario = models.OneToOneField('core.User', on_delete=models.CASCADE)
    usuario_soporte = models.BooleanField(default=True, verbose_name='¿Solicita Soporte?')

    class Meta:
        verbose_name = 'Perfil de Soporte'
        verbose_name_plural = 'Perfiles de Soporte'

    def __str__(self):
        return self.usuario.username


class TipoSoporte(StandardModel):
    nombre = models.CharField(max_length=100)

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Tipo de Soporte'
        verbose_name_plural = 'Tipos de Soportes'

    def __str__(self):
        return self.nombre


class Ticket(StandardModel):
    ESTADOS = (
        ('ABIERTO', 'Abierto'),
        ('EN_PROCESO', 'En Proceso'),
        ('ESPERA', 'En Espera'),
        ('CERRADO', 'Cerrado'),
        ('RECHAZADO', 'Rechazado'),
    )

    numero_ticket = models.CharField(max_length=20, unique=True, blank=True)
    establecimiento = models.ForeignKey('core.Establecimiento', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='tickets')
    asignado_a = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='tickets_asignados')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='ABIERTO')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    area_soporte = models.CharField(max_length=200,
                                    choices=[('MANTENCION', 'Mantencion'), ('INFORMATICA', 'Informatica')], null=True,
                                    blank=True)
    tipo_soporte = models.ForeignKey(TipoSoporte, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='tipo_soporte')
    solucion = models.TextField(null=True, blank=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    funcionario = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='funcionario')

    UPPERCASE_FIELDS = ['numero_ticket', 'titulo']
    LOWERCASE_FIELDS = ['solucion', ]

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.numero_ticket or f"Ticket #{self.id}"

    def create_number_ticket(self):
        alias_ticket = 'TCK'
        alias = 'TCK'
        year = timezone.now().year

        if self.establecimiento and self.establecimiento.alias:
            alias = self.establecimiento.alias.upper().strip()

        return f"{alias_ticket}-{year}-{alias}-{str(self.id).zfill(5)}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if is_new and not self.numero_ticket:
            # Primer save para obtener ID
            super().save(*args, **kwargs)

            # Generar número usando alias + ID global
            self.numero_ticket = self.create_number_ticket()

            # Segundo save solo para actualizar el número
            super().save(update_fields=['numero_ticket'])
            return

        super().save(*args, **kwargs)
