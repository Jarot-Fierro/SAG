from django.db import models

from core.standard.models import StandardModelEstablishment, StandardModel


class SolicitudCometidoViatico(StandardModelEstablishment):
    """
    Modelo unificado para Cometidos Funcionales y Solicitudes de Viáticos.
    Reemplaza SIAINGRESOCOMETIDO, SIAINGRESOVIATICO, SIAINGRESOCOMETIDORECHAZA y SIAINGRESOVIARECHAZA.
    """
    TIPO_SOLICITUD_CHOICES = [
        ('VIATICO', 'Viático'),
        ('COMETIDO', 'Cometido'),
    ]

    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('ENVIADO_JEFATURA', 'Enviado a Jefatura'),
        ('APROBADO_JEFE', 'Aprobado por Jefatura Directa'),
        ('EN_REVISION_SSGG', 'En Revisión Servicios Generales (Transporte)'),
        ('APROBADO_SSGG', 'Aprobado por Servicios Generales'),
        ('EN_REVISION_RRHH', 'En Revisión RRHH / Personal'),
        ('APROBADO_RRHH', 'Aprobado por RRHH'),
        ('RESOLUCION_EMITIDA', 'Resolución Emitida'),
        ('EN_PAGO', 'En Trámite de Pago / Finanzas'),
        ('PAGADO', 'Pagado'),
        ('RENDIDO', 'Rendido'),
        ('DEVUELTO', 'Devuelto para Corrección'),
        ('RECHAZADO', 'Rechazado'),
        ('ANULADO', 'Anulado'),
    ]

    folio = models.PositiveIntegerField(verbose_name="N° Folio Correlativo")
    ano = models.PositiveIntegerField(verbose_name="Año Presupuestario")
    tipo_solicitud = models.CharField(max_length=30, choices=TIPO_SOLICITUD_CHOICES, default='COMETIDO_VIATICO',
                                      verbose_name="Tipo de Solicitud")
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='BORRADOR', verbose_name="Estado Actual")

    # Funcionario y Dependencia (Integración con Core)
    funcionario = models.ForeignKey('core.Funcionario', on_delete=models.PROTECT, related_name="solicitudes_viatico",
                                    verbose_name="Funcionario Solicitante")
    unidad_organizacional = models.ForeignKey('core.UnidadOrganizacional', on_delete=models.PROTECT,
                                              related_name="solicitudes_viatico", verbose_name="Unidad / Depto.")
    cargo_desempenado = models.CharField(max_length=255, blank=True, null=True,
                                         verbose_name="Cargo al Momento de la Comisión")
    grado_funcionario = models.CharField(max_length=5, blank=True, null=True, verbose_name="Grado")

    # Justificación y Temporalidad General
    motivo_viaje = models.TextField(verbose_name="Motivo / Justificación del Cometido")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_termino = models.DateField(verbose_name="Fecha de Término")
    hora_salida = models.TimeField(verbose_name="Hora Salida")
    hora_llegada = models.TimeField(verbose_name="Hora Estimada Llegada")
    total_dias = models.PositiveIntegerField(default=1, verbose_name="Total Días Comisión")

    # Flags Operativos
    es_proyecto = models.BooleanField(default=False, verbose_name="¿Financiado con Fondos de Proyecto?")
    nombre_codigo_proyecto = models.CharField(max_length=255, blank=True, null=True,
                                              verbose_name="Nombre / Código Proyecto")
    es_urgente = models.BooleanField(default=False, verbose_name="¿Carácter Urgente / Prioritario?")
    tiene_derecho_pasaje = models.BooleanField(default=False, verbose_name="¿Tiene Derecho a Pasajes?")
    requiere_vehiculo_institucional = models.BooleanField(default=False,
                                                          verbose_name="¿Requiere Vehículo Institucional?")
    requiere_vales_bencina = models.BooleanField(default=False, verbose_name="¿Requiere Vales de Combustible?")

    # Control de Fechas Clave
    fecha_solicitud = models.DateTimeField(auto_now_add=True, verbose_name="Fecha Solicitud")
    fecha_aprobacion_jefe = models.DateTimeField(blank=True, null=True, verbose_name="Fecha Aprobación Jefe")
    fecha_aprobacion_rrhh = models.DateTimeField(blank=True, null=True, verbose_name="Fecha Aprobación RRHH")
    fecha_pago = models.DateField(blank=True, null=True, verbose_name="Fecha de Pago Efectiva")

    # Motivos de Devolución / Anulación
    motivo_rechazo_devolucion = models.TextField(blank=True, null=True, verbose_name="Motivo de Devolución / Rechazo")

    UPPERCASE_FIELDS = ['cargo_desempenado', 'nombre_codigo_proyecto']

    class Meta:
        verbose_name = "Solicitud de Cometido y Viático"
        verbose_name_plural = "Solicitudes de Cometidos y Viáticos"
        unique_together = ('folio', 'ano', 'establecimiento')
        ordering = ['-ano', '-folio']

    def __str__(self):
        return f"Folio {self.folio}/{self.ano} - {self.funcionario} ({self.get_estado_display()})"


class ItinerarioDestino(StandardModel):
    """
    MODELO CLAVE PARA EFICIENCIA (1:N):
    Registra cada uno de los lugares y tramos que componen el recorrido del cometido.
    Permite auditar el trayecto completo, tiempos por localidad y justificación de pernocta.
    """
    solicitud = models.ForeignKey(SolicitudCometidoViatico, on_delete=models.CASCADE, related_name="itinerarios",
                                  verbose_name="Solicitud de Viático")
    orden_visita = models.PositiveSmallIntegerField(default=1, verbose_name="Orden de Parada / Secuencia")

    lugar_destino = models.ForeignKey('viaticos.LugarDestino', on_delete=models.PROTECT,
                                      related_name="tramos_itinerario", verbose_name="Destino")
    descripcion_actividad_lugar = models.CharField(max_length=500, verbose_name="Actividad Específica en este Destino")

    fecha_llegada = models.DateField(verbose_name="Fecha Llegada")
    fecha_salida = models.DateField(verbose_name="Fecha Salida")

    # Categorización de Viático por Tramo
    pernocta_en_lugar = models.BooleanField(default=False, verbose_name="¿Pernocta en este lugar?")
    aplica_alimentacion_50 = models.BooleanField(default=False, verbose_name="¿Aplica 50% Alimentación?")
    aplica_faena = models.BooleanField(default=False, verbose_name="¿Aplica Tarifa Faena?")

    medio_transporte_tramo = models.CharField(
        max_length=50,
        choices=[
            ('VEHICULO_INSTITUCIONAL', 'Vehículo Institucional'),
            ('BUS_INTERURBANO', 'Bus Interurbano'),
            ('AVION', 'Avión'),
            ('VEHICULO_PARTICULAR', 'Vehículo Particular'),
            ('OTRO', 'Otro Transporte'),
        ],
        default='VEHICULO_INSTITUCIONAL',
        verbose_name="Medio de Transporte en Tramo"
    )

    class Meta:
        verbose_name = "Tramo de Itinerario"
        verbose_name_plural = "Tramos de Itinerario"
        ordering = ["solicitud", "orden_visita"]

    def __str__(self):
        return f"Parada #{self.orden_visita}: {self.lugar_destino} ({self.fecha_llegada} a {self.fecha_salida})"


class CalculoViatico(StandardModel):
    """
    Entidad 1:1 con la Solicitud para almacenar la liquidación y cálculo de montos.
    Garantiza inmutabilidad histórica una vez aprobada la resolución.
    """
    solicitud = models.OneToOneField(SolicitudCometidoViatico, on_delete=models.CASCADE,
                                     related_name="calculo_financiero", verbose_name="Solicitud")
    escala_aplicada = models.ForeignKey('viaticos.EscalaViatico', on_delete=models.PROTECT,
                                        verbose_name="Escala Tarifaria Aplicada")

    # Días y Valores 100% (Pernocta)
    dias_100 = models.PositiveIntegerField(default=0, verbose_name="Días 100% (Pernocta)")
    monto_unitario_100 = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                             verbose_name="Monto Unitario 100%")
    total_monto_100 = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Subtotal 100%")

    # Días y Valores 50% (Alimentación / Parcial)
    dias_50 = models.PositiveIntegerField(default=0, verbose_name="Días 50% (Parcial)")
    monto_unitario_50 = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                            verbose_name="Monto Unitario 50%")
    total_monto_50 = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Subtotal 50%")

    # Días y Valores Faena
    dias_faena = models.PositiveIntegerField(default=0, verbose_name="Días Faena")
    monto_unitario_faena = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                               verbose_name="Monto Unitario Faena")
    total_monto_faena = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Subtotal Faena")

    # Total Liquidado
    total_bruto_viatico = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                              verbose_name="Total Viático Liquidado ($)")
    monto_anticipo_entregado = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                                   verbose_name="Monto Anticipo ($)")
    saldo_a_pagar = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                        verbose_name="Saldo Final a Pagar ($)")

    class Meta:
        verbose_name = "Cálculo y Liquidación de Viático"
        verbose_name_plural = "Cálculos y Liquidaciones de Viáticos"

    def __str__(self):
        return f"Liquidación Solicitud #{self.solicitud.folio}: $ {self.total_bruto_viatico}"
