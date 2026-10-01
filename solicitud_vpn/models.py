from django.db import models, transaction
from django.utils import timezone

from config import settings
from core.standard.models import StandardModel


class PerfilVPN(StandardModel):
    """
    Perfil de gestión para el módulo de Solicitudes VPN.
    Permite determinar el acceso a la bandeja de gestión VPN y almacena
    los datos del técnico referente / informático del establecimiento.
    """
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_vpn',
        verbose_name='Usuario'
    )
    bandeja_vpn = models.BooleanField(
        default=True,
        verbose_name='Acceso a Bandeja de Gestión VPN'
    )

    # Datos del técnico referente del establecimiento (informático)
    nombre_completo = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Nombre Completo'
    )
    rut = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='RUT'
    )
    establecimiento = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Establecimiento'
    )
    telefono = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Teléfono'
    )
    cargo = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Cargo'
    )
    email = models.CharField(
        max_length=254,
        blank=True,
        null=True,
        verbose_name='Email'
    )

    UPPERCASE_FIELDS = ['rut', 'nombre_completo']
    LOWERCASE_FIELDS = ['email']

    class Meta:
        verbose_name = 'Perfil de Gestión VPN'
        verbose_name_plural = 'Perfiles de Gestión VPN'
        ordering = ['-id']

    def __str__(self):
        return f"Perfil VPN: {self.usuario.get_full_name() or self.usuario.username}"


class SolicitudVPN(StandardModel):
    """
    Solicitud de acceso VPN para establecimientos del Servicio de Salud Arauco.
    Almacena los datos del solicitante/técnico, requerimientos generales y datos VPN.
    """
    ESTADOS = (
        ('BORRADOR', 'Borrador'),
        ('PENDIENTE', 'Pendiente'),
        ('EN_REVISION', 'En revisión'),
        ('ENVIADO_ECONECTA', 'Enviado a eConecta'),
        ('COMPLETADO', 'Completado'),
        ('RECHAZADO', 'Rechazado'),
    )

    ACCIONES = (
        ('CREAR', 'Crear'),
        ('ACTUALIZAR', 'Actualizar'),
        ('ELIMINAR', 'Eliminar'),
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
        related_name='solicitudes_vpn',
        verbose_name='Establecimiento Solicitante'
    )
    departamento_solicitante = models.ForeignKey(
        'core.UnidadOrganizacional',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitudes_vpn_depto',
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
        related_name='solicitudes_vpn_creadas',
        verbose_name='Usuario Solicitante'
    )
    fecha_solicitud = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Solicitud'
    )
    accion = models.CharField(
        max_length=20,
        choices=ACCIONES,
        default='CREAR',
        verbose_name='Acción Solicitada'
    )
    estado = models.CharField(
        max_length=30,
        choices=ESTADOS,
        default='PENDIENTE',
        verbose_name='Estado'
    )

    # Datos del Técnico / Solicitante (almacenados en texto plano para histórico)
    tecnico_nombre = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Nombre Completo Técnico'
    )
    tecnico_rut = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='RUT Técnico'
    )
    tecnico_establecimiento = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Establecimiento Técnico'
    )
    tecnico_telefono = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Teléfono Técnico'
    )
    tecnico_cargo = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Cargo Técnico'
    )
    tecnico_email = models.CharField(
        max_length=254,
        blank=True,
        null=True,
        verbose_name='Email Técnico'
    )
    tecnico_fecha = models.DateField(
        default=timezone.now,
        verbose_name='Fecha Requerimiento Técnico'
    )
    es_proveedor = models.BooleanField(
        default=False,
        verbose_name='¿Es proveedor / empresa tercera?'
    )

    # Datos Técnicos VPN
    grupo_vpn = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='Nombre del Grupo VPN'
    )
    fecha_expiracion = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Expiración'
    )
    timeout_vpn = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        default='1 hora',
        verbose_name='Time Out VPN'
    )
    observacion = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observación / Descripción General'
    )

    accesos = models.ManyToManyField(
        'AccesoVPN',
        blank=True,
        related_name='solicitudes_vpn',
        verbose_name='Accesos VPN'
    )

    # Gestión y Revisión TIC (para posterior solicitud en eConecta)
    usuario_revision = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitudes_vpn_revisadas',
        verbose_name='Usuario Revisor TIC'
    )
    fecha_revision = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha Revisión TIC'
    )
    fecha_envio_econecta = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha Envío a eConecta'
    )
    fecha_finalizacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha Finalización'
    )
    ticket_econecta = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Ticket / ID eConecta'
    )
    observacion_revision = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observación de Revisión / Gestión'
    )

    UPPERCASE_FIELDS = ['numero_solicitud', 'tecnico_rut', 'ticket_econecta']
    LOWERCASE_FIELDS = ['tecnico_email']

    class Meta:
        verbose_name = 'Solicitud VPN'
        verbose_name_plural = 'Solicitudes VPN'
        ordering = ['-id']
        permissions = [
            ('can_manage_vpn', 'Puede gestionar solicitudes VPN en Bandeja TIC'),
        ]

    def __str__(self):
        return self.numero_solicitud or f"Solicitud VPN #{self.id}"

    def generar_folio(self):
        year = timezone.now().year
        alias = 'VPN'
        if self.establecimiento:
            alias = self.establecimiento.alias or self.establecimiento.nombre.upper().strip()[:4]
        prefix = f"VPN-{year}-{alias}-"

        with transaction.atomic():
            last = SolicitudVPN.objects.filter(
                numero_solicitud__startswith=prefix
            ).order_by('-numero_solicitud').first()

            if last and last.numero_solicitud:
                try:
                    num = int(last.numero_solicitud.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = SolicitudVPN.objects.filter(
                        establecimiento=self.establecimiento
                    ).count() + 1
            else:
                num = 1

            return f"{prefix}{str(num).zfill(5)}"

    @property
    def total_beneficiarios(self):
        return self.beneficiarios.count()

    @property
    def total_accesos(self):
        return self.accesos.count()

    def save(self, *args, **kwargs):
        if not self.pk and not self.numero_solicitud:
            self.numero_solicitud = self.generar_folio()

        if self.departamento_solicitante and not self.departamento_nombre:
            self.departamento_nombre = str(self.departamento_solicitante)

        super().save(*args, **kwargs)


class BeneficiarioVPN(StandardModel):
    """
    Beneficiario incluido en una solicitud VPN.
    Contiene referencia opcional al Funcionario y snapshot histórico de sus datos.
    """
    solicitud = models.ForeignKey(
        SolicitudVPN,
        on_delete=models.CASCADE,
        related_name='beneficiarios',
        verbose_name='Solicitud'
    )
    funcionario = models.ForeignKey(
        'core.Funcionario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='beneficiarios_vpn',
        verbose_name='Funcionario Existente'
    )

    # Datos históricos del beneficiario
    rut = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='RUT'
    )
    nombres = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='Nombres'
    )
    apellidos = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='Apellidos'
    )
    nombre_completo = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Nombre Completo'
    )
    establecimiento = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Establecimiento'
    )
    telefono = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Teléfono'
    )
    cargo = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Cargo'
    )
    fecha = models.DateField(
        default=timezone.now,
        verbose_name='Fecha'
    )
    email = models.CharField(
        max_length=254,
        blank=True,
        null=True,
        verbose_name='Email'
    )

    UPPERCASE_FIELDS = ['rut', 'nombres', 'apellidos', 'nombre_completo']
    LOWERCASE_FIELDS = ['email']

    class Meta:
        verbose_name = 'Beneficiario VPN'
        verbose_name_plural = 'Beneficiarios VPN'
        ordering = ['id']

    def __str__(self):
        return f"{self.get_nombre_completo()} ({self.solicitud.numero_solicitud or self.solicitud_id})"

    def get_nombre_completo(self):
        if self.nombre_completo:
            return self.nombre_completo
        nombre = f"{self.nombres or ''} {self.apellidos or ''}".strip()
        if nombre:
            return nombre
        return self.rut or f"Beneficiario #{self.id or 'Nuevo'}"

    def aplicar_snapshot_funcionario(self):
        """
        Copia los datos del Funcionario asociado a los campos snapshot si están vacíos.
        """
        if self.funcionario:
            if not self.rut and self.funcionario.rut:
                self.rut = self.funcionario.rut
            if not self.nombres and self.funcionario.nombres:
                self.nombres = self.funcionario.nombres
            if not self.apellidos and self.funcionario.apellidos:
                self.apellidos = self.funcionario.apellidos
            if not self.nombre_completo:
                self.nombre_completo = self.funcionario.nombre or f"{self.funcionario.nombres or ''} {self.funcionario.apellidos or ''}".strip()
            if not self.cargo and self.funcionario.cargo:
                self.cargo = self.funcionario.cargo
            if not self.establecimiento and self.funcionario.establecimiento:
                self.establecimiento = self.funcionario.establecimiento.nombre
            if not self.email and self.funcionario.email:
                self.email = self.funcionario.email

    def save(self, *args, **kwargs):
        if not self.nombre_completo:
            self.nombre_completo = f"{self.nombres or ''} {self.apellidos or ''}".strip()
        if not self.pk or self.funcionario:
            self.aplicar_snapshot_funcionario()
        super().save(*args, **kwargs)


class AccesoVPN(StandardModel):
    """
    Mantenedor y catálogo de accesos a sistemas y direcciones IP / segmentos.
    """
    plataforma = models.CharField(
        max_length=255,
        verbose_name='Plataforma / Sistema / Recurso'
    )
    ip = models.CharField(
        max_length=100,
        verbose_name='Dirección IP o Segmento'
    )

    class Meta:
        verbose_name = 'Acceso VPN'
        verbose_name_plural = 'Accesos VPN'
        ordering = ['plataforma', 'ip']

    def __str__(self):
        return f"{self.plataforma} ({self.ip})"
