from django.db import models, transaction
from django.utils import timezone
from config import settings
from core.standard.models import StandardModel


class AreaSolicitud(StandardModel):
    nombre = models.CharField(max_length=150, unique=True, verbose_name="Nombre del Área")
    codigo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    UPPERCASE_FIELDS = ['nombre', 'codigo']

    class Meta:
        verbose_name = "Área de Solicitud"
        verbose_name_plural = "Áreas de Solicitud"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class SubareaSolicitud(StandardModel):
    area = models.ForeignKey(
        AreaSolicitud,
        on_delete=models.CASCADE,
        related_name="subareas",
        verbose_name="Área"
    )
    nombre = models.CharField(max_length=150, verbose_name="Nombre de la Subárea")
    codigo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    UPPERCASE_FIELDS = ['nombre', 'codigo']

    class Meta:
        verbose_name = "Subárea de Solicitud"
        verbose_name_plural = "Subáreas de Solicitud"
        ordering = ["area__nombre", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=['area', 'nombre'], name='unique_subarea_por_area')
        ]

    def __str__(self):
        return f"{self.area.nombre} - {self.nombre}"


class MaestraCodigoSISSA(StandardModel):
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código SISSA")
    nombre_producto = models.CharField(max_length=255, verbose_name="Nombre / Producto Base")
    presentacion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Presentación")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    area = models.ForeignKey(
        AreaSolicitud,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="codigos_maestra",
        verbose_name="Área"
    )
    subarea = models.ForeignKey(
        SubareaSolicitud,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="codigos_maestra",
        verbose_name="Subárea"
    )

    UPPERCASE_FIELDS = ['codigo', 'nombre_producto', 'presentacion']

    class Meta:
        verbose_name = "Código Maestra SISSA"
        verbose_name_plural = "Códigos Maestra SISSA"
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre_producto}"


class PerfilCodigo(StandardModel):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_codigo",
        verbose_name="Usuario"
    )
    es_referente = models.BooleanField(
        default=False,
        verbose_name="¿Es Referente?"
    )
    es_referente_global = models.BooleanField(
        default=False,
        verbose_name="¿Es Referente Global (Todas las Áreas)?"
    )
    areas_asignadas = models.ManyToManyField(
        AreaSolicitud,
        blank=True,
        related_name="referentes",
        verbose_name="Áreas Asignadas"
    )
    puede_validar = models.BooleanField(
        default=False,
        verbose_name="¿Puede Validar / Rechazar Solicitudes?"
    )
    puede_crear_codigos = models.BooleanField(
        default=False,
        verbose_name="¿Puede Registrar Creación Efectiva de Códigos?"
    )
    puede_solicitar = models.BooleanField(
        default=True,
        verbose_name="¿Puede Crear Solicitudes?"
    )

    class Meta:
        verbose_name = "Perfil de Gestión de Códigos"
        verbose_name_plural = "Perfiles de Gestión de Códigos"

    def __str__(self):
        return f"Perfil Códigos: {self.usuario}"

    def tiene_acceso_area(self, area):
        if not self.es_referente:
            return False
        if self.es_referente_global:
            return True
        if not area:
            return False
        return self.areas_asignadas.filter(id=area.id).exists()

    def puede_gestionar_solicitud(self, solicitud):
        if not self.es_referente:
            return False
        if self.es_referente_global:
            return True
        if not solicitud.area:
            return False
        return self.areas_asignadas.filter(id=solicitud.area.id).exists()


class SolicitudCodigo(StandardModel):
    ESTADO_PENDIENTE_VALIDACION = 'PENDIENTE_VALIDACION'
    ESTADO_OBSERVADA = 'OBSERVADA'
    ESTADO_VALIDADA = 'VALIDADA'
    ESTADO_PENDIENTE_CREACION = 'PENDIENTE_CREACION'
    ESTADO_RECHAZADA = 'RECHAZADA'
    ESTADO_CODIGO_CREADO = 'CODIGO_CREADO'

    ESTADOS = (
        (ESTADO_PENDIENTE_VALIDACION, 'Pendiente de Validación'),
        (ESTADO_OBSERVADA, 'Observada'),
        (ESTADO_VALIDADA, 'Validada'),
        (ESTADO_PENDIENTE_CREACION, 'Pendiente de Creación'),
        (ESTADO_RECHAZADA, 'Rechazada'),
        (ESTADO_CODIGO_CREADO, 'Código Creado'),
    )

    numero_solicitud = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Folio / Número de Solicitud"
    )
    usuario_solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="solicitudes_codigo_creadas",
        verbose_name="Usuario Solicitante"
    )
    establecimiento = models.ForeignKey(
        'core.Establecimiento',
        on_delete=models.PROTECT,
        related_name="solicitudes_codigo",
        verbose_name="Establecimiento de Origen"
    )
    area = models.ForeignKey(
        AreaSolicitud,
        on_delete=models.PROTECT,
        related_name="solicitudes",
        verbose_name="Área"
    )
    subarea = models.ForeignKey(
        SubareaSolicitud,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes",
        verbose_name="Subárea"
    )
    descripcion_requerimiento = models.TextField(
        verbose_name="Descripción del Requerimiento"
    )
    producto_base = models.CharField(
        max_length=255,
        verbose_name="Producto Base"
    )
    presentacion = models.CharField(
        max_length=255,
        verbose_name="Presentación"
    )
    antecedentes_complementarios = models.TextField(
        blank=True,
        null=True,
        verbose_name="Antecedentes Complementarios / Justificación"
    )
    estado = models.CharField(
        max_length=30,
        choices=ESTADOS,
        default=ESTADO_PENDIENTE_VALIDACION,
        db_index=True,
        verbose_name="Estado"
    )
    fecha_solicitud = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de Solicitud"
    )
    fecha_observacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha Observación"
    )
    fecha_reenvio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha Reenvío"
    )
    fecha_validacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha Validación"
    )
    fecha_rechazo = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha Rechazo"
    )
    fecha_creacion_codigo = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha Creación de Código"
    )
    observaciones_referente = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones del Referente"
    )
    motivo_rechazo = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motivo de Rechazo"
    )
    usuario_referente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes_codigo_revisadas",
        verbose_name="Referente Responsable"
    )
    codigo_creado = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Código SISSA Creado"
    )
    observaciones_creacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones de Creación"
    )
    usuario_creador_codigo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes_codigo_creadas_final",
        verbose_name="Usuario que Creó el Código"
    )

    UPPERCASE_FIELDS = ['numero_solicitud', 'producto_base', 'presentacion', 'codigo_creado']

    class Meta:
        verbose_name = "Solicitud de Código SISSA"
        verbose_name_plural = "Solicitudes de Códigos SISSA"
        ordering = ["-fecha_solicitud", "-id"]
        permissions = [
            ('can_create_solicitud', 'Puede crear solicitudes de código'),
            ('can_view_mis_solicitudes', 'Puede ver sus propias solicitudes de código'),
            ('can_review_referente', 'Puede revisar solicitudes en bandeja de referente'),
            ('can_validate_solicitud', 'Puede validar solicitudes de código'),
            ('can_reject_solicitud', 'Puede rechazar solicitudes de código'),
            ('can_observe_solicitud', 'Puede observar solicitudes de código'),
            ('can_edit_observada', 'Puede corregir y reenviar solicitudes observadas'),
            ('can_create_final_code', 'Puede registrar código creado y finalizar solicitud'),
        ]

    def __str__(self):
        return self.numero_solicitud or f"Solicitud #{self.id}"

    def generar_folio(self):
        year = timezone.now().year
        alias = 'DIR'
        if self.establecimiento:
            if self.establecimiento.alias:
                alias = self.establecimiento.alias.strip().upper()
            elif self.establecimiento.nombre:
                alias = self.establecimiento.nombre.strip().upper()[:4]
        prefix = f"COD-{year}-{alias}-"

        with transaction.atomic():
            last = SolicitudCodigo.objects.filter(
                numero_solicitud__startswith=prefix
            ).order_by('-numero_solicitud').first()

            if last and last.numero_solicitud:
                try:
                    num = int(last.numero_solicitud.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = SolicitudCodigo.objects.filter(establecimiento=self.establecimiento).count() + 1
            else:
                num = 1

            return f"{prefix}{str(num).zfill(5)}"

    def registrar_evento(self, usuario, accion, estado_anterior, estado_nuevo, detalle=""):
        return HistorialSolicitudCodigo.objects.create(
            solicitud=self,
            usuario=usuario,
            accion=accion,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            detalle=detalle
        )

    def puede_ser_editada_por(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.usuario_solicitante_id == user.id and self.estado == self.ESTADO_OBSERVADA

    def puede_ser_revisada_por(self, user):
        if not user or not user.is_authenticated:
            return False
        perfil = getattr(user, 'perfil_codigo', None)
        if not perfil or not perfil.es_referente:
            return False
        return perfil.puede_gestionar_solicitud(self)

    def puede_crear_codigo_usuario(self, user):
        if not user or not user.is_authenticated:
            return False
        perfil = getattr(user, 'perfil_codigo', None)
        if not perfil:
            return False
        return perfil.puede_crear_codigos


class HistorialSolicitudCodigo(models.Model):
    solicitud = models.ForeignKey(
        SolicitudCodigo,
        on_delete=models.CASCADE,
        related_name="historial_eventos",
        verbose_name="Solicitud"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuario Responsable"
    )
    accion = models.CharField(
        max_length=100,
        verbose_name="Acción Realizada"
    )
    estado_anterior = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Estado Anterior"
    )
    estado_nuevo = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Estado Nuevo"
    )
    detalle = models.TextField(
        blank=True,
        null=True,
        verbose_name="Detalle / Justificación / Observaciones"
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y Hora"
    )

    class Meta:
        verbose_name = "Historial de Solicitud de Código"
        verbose_name_plural = "Historiales de Solicitudes de Código"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"{self.solicitud.numero_solicitud} - {self.accion} ({self.fecha:%Y-%m-%d %H:%M})"
