from django.db import models

from core.standard.models import StandardModel


class GastoTransporte(StandardModel):
    """
    Unifica SIAPASAJES y SIAPASAJESAE en un único modelo escalable para traslados,
    pasajes aéreos/terrestres, reembolsos de peajes, estacionamiento y combustible.
    """
    TIPO_GASTO_CHOICES = [
        ('AEREO', 'Pasaje Aéreo Comercial'),
        ('BUS_FERROCARRIL', 'Pasaje Bus / Ferrocarril'),
        ('VALE_COMBUSTIBLE', 'Vale de Combustible Institucional'),
        ('REEMBOLSO_BENCINA', 'Reembolso Combustible Vehículo Particular'),
        ('PEAJE_ESTACIONAMIENTO', 'Peajes y Estacionamientos'),
        ('OTRO_TRANSPORTE', 'Otro Tipo de Transporte'),
    ]

    solicitud = models.ForeignKey('viaticos.SolicitudCometidoViatico', on_delete=models.CASCADE,
                                  related_name="gastos_transporte", verbose_name="Solicitud")
    tipo_gasto = models.CharField(max_length=30, choices=TIPO_GASTO_CHOICES, verbose_name="Tipo de Gasto / Pasaje")

    # Detalle General de Trayecto
    origen = models.CharField(max_length=150, verbose_name="Origen")
    destino = models.CharField(max_length=150, verbose_name="Destino")
    fecha_ida = models.DateField(verbose_name="Fecha Ida")
    fecha_regreso = models.DateField(blank=True, null=True, verbose_name="Fecha Regreso")

    # Datos Específicos para Transporte Aéreo
    aerolinea = models.CharField(max_length=100, blank=True, null=True, verbose_name="Línea Aérea")
    codigo_reserva_pnr = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código de Reserva / PNR")
    numero_billete = models.CharField(max_length=100, blank=True, null=True, verbose_name="N° Billete / Ticket")

    # Datos Específicos para Combustible y Vehículo
    numero_vale_bencina = models.CharField(max_length=100, blank=True, null=True,
                                           verbose_name="N° de Vale(s) Combustible")
    tipo_combustible = models.CharField(max_length=50, blank=True, null=True,
                                        verbose_name="Tipo Combustible (93/95/97/Diesel)")
    kilometros_recorridos = models.PositiveIntegerField(default=0, verbose_name="Kilómetros Estimados / Recorridos")
    precio_por_litro = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                           verbose_name="Precio por Litro ($)")

    # Montos y Rendición
    monto_cotizado = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                         verbose_name="Monto Cotizado / Autorizado ($)")
    monto_real_ejecutado = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                               verbose_name="Monto Real Ejecutado ($)")
    pagado_directo_proveedor = models.BooleanField(default=False,
                                                   verbose_name="¿Pagado por Orden de Compra Institucional?")

    class Meta:
        verbose_name = "Gasto de Transporte y Pasaje"
        verbose_name_plural = "Gastos de Transporte y Pasajes"
        ordering = ["fecha_ida"]

    def __str__(self):
        return f"{self.get_tipo_gasto_display()} - {self.origen} a {self.destino} ($ {self.monto_real_ejecutado or self.monto_cotizado})"
