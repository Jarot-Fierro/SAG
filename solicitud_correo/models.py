from django.db import models, transaction
from django.utils import timezone

from config import settings
from core.standard.models import StandardModel


class PerfilCorreo(StandardModel):
    PERMISION_CHOICES = [
        (0, 'Sin Acceso'),
        (1, 'Con Acceso'),
    ]

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_correo',
        verbose_name='Usuario'
    )
    bandeja_rrhh = models.IntegerField(
        choices=PERMISION_CHOICES,
        default=0,
        verbose_name='Bandeja RR.HH.'
    )
    bandeja_tic = models.IntegerField(
        choices=PERMISION_CHOICES,
        default=0,
        verbose_name='Bandeja TIC'
    )



class SolicitudCorreo(StandardModel):
    ESTADOS = (
        ('BORRADOR', 'Borrador'),
        ('PENDIENTE_RRHH', 'Pendiente de revisión de RR.HH.'),
        ('EN_REVISION_RRHH', 'En revisión RR.HH.'),
        ('EN_TIC', 'Enviada a TIC'),
        ('EN_PROCESO_TIC', 'En proceso TIC'),
        ('FINALIZADA', 'Finalizada'),
        ('CANCELADA', 'Cancelada'),
    )

    numero_solicitud = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Número / Folio de Solicitud'
    )
    establecimiento = models.ForeignKey(
        'core.Establecimiento',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='solicitudes_correo',
        verbose_name='Establecimiento'
    )
    departamento_solicitante = models.ForeignKey(
        'core.UnidadOrganizacional',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitudes_correo_depto',
        verbose_name='Departamento Solicitante'
    )
    departamento_nombre = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Nombre Departamento'
    )
    usuario_solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='solicitudes_correo_creadas',
        verbose_name='Usuario Solicitante'
    )
    fecha_solicitud = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Solicitud'
    )
    estado = models.CharField(
        max_length=30,
        choices=ESTADOS,
        default='PENDIENTE_RRHH',
        verbose_name='Estado'
    )
    observacion = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observación'
    )

    # Fechas relevantes del flujo
    fecha_revision_rrhh = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha Revisión RR.HH.'
    )
    fecha_envio_tic = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha Envío a TIC'
    )
    fecha_procesamiento_tic = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha Procesamiento TIC'
    )
    fecha_finalizacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha Finalización'
    )

    # Usuarios que realizaron las revisiones correspondientes
    usuario_rrhh = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitudes_correo_revisadas_rrhh',
        verbose_name='Usuario Revisor RR.HH.'
    )
    tecnico_tic = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitudes_correo_procesadas_tic',
        verbose_name='Técnico TIC'
    )

    UPPERCASE_FIELDS = ['numero_solicitud']

    class Meta:
        verbose_name = 'Solicitud de Correo'
        verbose_name_plural = 'Solicitudes de Correos'
        ordering = ['-id']
        permissions = [
            ('can_review_rrhh', 'Puede revisar solicitudes en RR.HH.'),
            ('can_process_tic', 'Puede procesar solicitudes en TIC'),
            ('can_notify_funcionario', 'Puede registrar notificaciones a funcionarios'),
        ]

    def __str__(self):
        return self.numero_solicitud or f"Solicitud #{self.id}"

    def generar_folio(self):
        year = timezone.now().year
        alias = 'GEN'
        if self.establecimiento:
            alias = self.establecimiento.alias or self.establecimiento.nombre.upper().strip()[:4]
        prefix = f"SOL-{year}-{alias}-"

        with transaction.atomic():
            last = SolicitudCorreo.objects.filter(
                numero_solicitud__startswith=prefix
            ).order_by('-numero_solicitud').first()

            if last and last.numero_solicitud:
                try:
                    num = int(last.numero_solicitud.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = SolicitudCorreo.objects.filter(
                        establecimiento=self.establecimiento
                    ).count() + 1
            else:
                num = 1

            return f"{prefix}{str(num).zfill(5)}"

    def actualizar_estado_general(self, save=True):
        """
        Calcula y actualiza el estado general de la solicitud según los estados de sus detalles.
        """
        if self.estado in ['BORRADOR', 'CANCELADA']:
            return self.estado

        detalles = list(self.detalles.all())
        if not detalles:
            return self.estado

        total = len(detalles)
        pendientes_rrhh = sum(1 for d in detalles if d.estado == 'PENDIENTE_RRHH')
        aprobados_rrhh = sum(1 for d in detalles if d.estado == 'APROBADO_RRHH')
        rechazados_rrhh = sum(1 for d in detalles if d.estado == 'RECHAZADO_RRHH')
        en_proceso_tic = sum(1 for d in detalles if d.estado == 'EN_PROCESO_TIC')
        creados = sum(1 for d in detalles if d.estado == 'CREADO')
        errores = sum(1 for d in detalles if d.estado == 'ERROR')

        # Si todos fueron rechazados por RR.HH.
        if rechazados_rrhh == total:
            self.estado = 'FINALIZADA'
            if not self.fecha_finalizacion:
                self.fecha_finalizacion = timezone.now()
        # Si aún no se revisa ninguno
        elif pendientes_rrhh == total:
            self.estado = 'PENDIENTE_RRHH'
        # Si está en proceso de revisión de RR.HH. (hay pendientes y algunos revisados)
        elif pendientes_rrhh > 0 and (aprobados_rrhh > 0 or rechazados_rrhh > 0):
            self.estado = 'EN_REVISION_RRHH'
        # Si ya se revisaron todos en RR.HH. (pendientes_rrhh == 0)
        elif pendientes_rrhh == 0:
            # Si todos los procesables (aprobados) ya finalizaron en CREADO o ERROR
            pendientes_en_tic = aprobados_rrhh + en_proceso_tic
            if pendientes_en_tic == 0 and (creados + errores + rechazados_rrhh == total):
                self.estado = 'FINALIZADA'
                if not self.fecha_finalizacion:
                    self.fecha_finalizacion = timezone.now()
            elif en_proceso_tic > 0 or creados > 0 or errores > 0:
                self.estado = 'EN_PROCESO_TIC'
            else:
                self.estado = 'EN_TIC'
                if not self.fecha_envio_tic:
                    self.fecha_envio_tic = timezone.now()

        if save:
            self.save(update_fields=['estado', 'fecha_finalizacion', 'fecha_envio_tic', 'updated_at'])

        return self.estado

    @property
    def total_funcionarios(self):
        return self.detalles.count()

    @property
    def total_aprobados(self):
        return self.detalles.filter(estado__in=['APROBADO_RRHH', 'EN_PROCESO_TIC', 'CREADO']).count()

    @property
    def total_rechazados(self):
        return self.detalles.filter(estado='RECHAZADO_RRHH').count()

    @property
    def total_creados(self):
        return self.detalles.filter(estado='CREADO').count()

    @property
    def total_pendientes_rrhh(self):
        return self.detalles.filter(estado='PENDIENTE_RRHH').count()

    @property
    def total_pendientes_tic(self):
        return self.detalles.filter(estado__in=['APROBADO_RRHH', 'EN_PROCESO_TIC']).count()

    def save(self, *args, **kwargs):
        if not self.pk and not self.numero_solicitud:
            self.numero_solicitud = self.generar_folio()

        if self.departamento_solicitante and not self.departamento_nombre:
            self.departamento_nombre = str(self.departamento_solicitante)

        super().save(*args, **kwargs)


class SolicitudCorreoDetalle(StandardModel):
    ESTADOS = (
        ('PENDIENTE_RRHH', 'Pendiente RR.HH.'),
        ('APROBADO_RRHH', 'Aprobado RR.HH.'),
        ('RECHAZADO_RRHH', 'Rechazado RR.HH.'),
        ('EN_PROCESO_TIC', 'En proceso TIC'),
        ('CREADO', 'Creado'),
        ('ERROR', 'Error'),
    )

    solicitud = models.ForeignKey(
        SolicitudCorreo,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name='Solicitud'
    )
    funcionario = models.ForeignKey(
        'core.Funcionario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalles_solicitud_correo',
        verbose_name='Funcionario'
    )

    # Snapshot histórico de datos básicos del funcionario
    rut = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='RUT'
    )
    nombres = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name='Nombres'
    )
    apellidos = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name='Apellidos'
    )
    departamento = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Departamento'
    )
    cargo = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Cargo'
    )

    # Estado individual
    estado = models.CharField(
        max_length=30,
        choices=ESTADOS,
        default='PENDIENTE_RRHH',
        verbose_name='Estado Individual'
    )
    motivo_rechazo = models.TextField(
        null=True,
        blank=True,
        verbose_name='Motivo de Rechazo'
    )

    # Revisión RR.HH.
    usuario_rrhh = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalles_correo_revisados_rrhh',
        verbose_name='Usuario que revisó en RR.HH.'
    )
    fecha_revision_rrhh = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha Revisión RR.HH.'
    )

    # Procesamiento TIC
    tecnico_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalles_correo_tecnico_tic',
        verbose_name='Técnico Responsable TIC'
    )
    fecha_procesamiento_tic = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha Procesamiento TIC'
    )
    referencia_externa = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Referencia Solicitud Externa / MINSAL'
    )
    fecha_creacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Creación'
    )
    correo_creado = models.CharField(
        max_length=254,
        null=True,
        blank=True,
        verbose_name='Correo Creado'
    )
    observacion_tic = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observación TIC'
    )

    # Datos relacionados con la notificación al funcionario
    notificado = models.BooleanField(
        default=False,
        verbose_name='¿Notificado?'
    )
    fecha_notificacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Notificación'
    )
    notificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalles_correo_notificados',
        verbose_name='Notificado Por'
    )
    observacion_notificacion = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observación de Notificación'
    )
    correo_notificacion_enviado_a = models.CharField(
        max_length=254,
        null=True,
        blank=True,
        verbose_name='Correo Destinatario Notificación'
    )

    UPPERCASE_FIELDS = ['rut', 'nombres', 'apellidos', 'referencia_externa']
    LOWERCASE_FIELDS = ['correo_creado', 'correo_notificacion_enviado_a']

    class Meta:
        verbose_name = 'Detalle de Solicitud de Correo'
        verbose_name_plural = 'Detalles de Solicitudes de Correos'
        ordering = ['id']

    def __str__(self):
        return f"{self.nombre_completo} ({self.solicitud.numero_solicitud or self.solicitud_id})"

    @property
    def nombre_completo(self):
        nombre = f"{self.nombres or ''} {self.apellidos or ''}".strip()
        if nombre:
            return nombre
        return self.rut or f"Funcionario #{self.id or 'Nuevo'}"

    def aplicar_snapshot_funcionario(self):
        """
        Copia los datos del funcionario a los campos snapshot si están vacíos.
        """
        if self.funcionario:
            if not self.rut and self.funcionario.rut:
                self.rut = self.funcionario.rut
            if not self.nombres and self.funcionario.nombres:
                self.nombres = self.funcionario.nombres
            if not self.apellidos and self.funcionario.apellidos:
                self.apellidos = self.funcionario.apellidos
            if not self.cargo and self.funcionario.cargo:
                self.cargo = self.funcionario.cargo
            if not self.departamento and self.funcionario.unidad_organizacional:
                self.departamento = str(self.funcionario.unidad_organizacional)

    def save(self, *args, **kwargs):
        # Si es un nuevo registro o se especificó funcionario, aplicamos el snapshot
        if not self.pk or self.funcionario:
            self.aplicar_snapshot_funcionario()

        super().save(*args, **kwargs)
