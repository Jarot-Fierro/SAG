from django.db import models, transaction
from django.utils import timezone

from core.standard.models import StandardModel


class TicketConfig(StandardModel):
    establecimiento = models.OneToOneField('core.Establecimiento', on_delete=models.CASCADE,
                                           related_name='ticket_config')
    ultimo_correlativo = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Configuración de Ticket'
        verbose_name_plural = 'Configuraciones de Tickets'

    def __str__(self):
        return f"Configuración para {self.establecimiento.nombre}"


class PerfilSoporte(StandardModel):
    nombre = models.CharField(max_length=100)
    usuario = models.ManyToManyField('core.User', blank=True, verbose_name="Usuarios",
                                     related_name='perfil_soporte_usuario')
    usuario_soporte = models.BooleanField(default=True, verbose_name='¿Solicita Soporte?')

    class Meta:
        verbose_name = 'Perfil de Soporte'
        verbose_name_plural = 'Perfiles de Soporte'

    def __str__(self):
        return self.nombre


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

    numero_ticket = models.CharField(max_length=20, unique=True, null=True, blank=True)
    establecimiento = models.ForeignKey('core.Establecimiento', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='tickets')
    departamento = models.ForeignKey('core.Departamento', on_delete=models.SET_NULL, null=True, blank=True,
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

    def save(self, *args, **kwargs):
        if not self.pk and not self.numero_ticket:
            with transaction.atomic():
                # Obtenemos o creamos la configuración para el establecimiento
                # Bloqueamos la fila con select_for_update para manejar la concurrencia
                config, created = TicketConfig.objects.select_for_update().get_or_create(
                    establecimiento=self.establecimiento
                )

                # Incrementamos el correlativo
                config.ultimo_correlativo += 1
                config.save()

                # Generamos el número de ticket
                alias_ticket = 'TCK'
                year = timezone.now().year
                alias = 'SP'
                if self.establecimiento:
                    alias = self.establecimiento.alias or self.establecimiento.nombre.upper().strip()

                self.numero_ticket = f"{alias_ticket}-{year}-{alias}-{str(config.ultimo_correlativo).zfill(5)}"

        super().save(*args, **kwargs)
