from django.db import models

from core.standard.models import StandardModelEstablishment, StandardModel


class EgresoPagoViatico(StandardModelEstablishment):
    """
    Control de egreso de fondos, emisión de cheques, transferencias bancarias y despachos.
    Reemplaza SIAEGRESOS y SIADESPACHO.
    """
    MEDIO_PAGO_CHOICES = [
        ('TRANSFERENCIA', 'Transferencia Electrónica'),
        ('CHEQUE', 'Cheque Nominativo'),
        ('EFECTIVO_CAJA_CHICA', 'Efectivo / Caja Chica'),
    ]

    solicitud = models.ForeignKey('viaticos.SolicitudCometidoViatico', on_delete=models.PROTECT,
                                  related_name="egresos_pago", verbose_name="Solicitud")
    numero_egreso = models.PositiveIntegerField(verbose_name="N° Egreso Presupuestario")
    ano_egreso = models.PositiveIntegerField(verbose_name="Año Egreso")

    medio_pago = models.CharField(max_length=30, choices=MEDIO_PAGO_CHOICES, default='TRANSFERENCIA',
                                  verbose_name="Medio de Pago")
    monto_total_pagado = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto Total Pagado ($)")

    # Datos de Cheque o Transferencia
    id_transferencia_bancaria = models.CharField(max_length=100, blank=True, null=True,
                                                 verbose_name="ID / N° Transferencia")
    numero_cheque = models.CharField(max_length=50, blank=True, null=True, verbose_name="N° de Cheque")
    banco_origen = models.CharField(max_length=100, blank=True, null=True, verbose_name="Banco Origen")
    cuenta_origen = models.CharField(max_length=50, blank=True, null=True, verbose_name="N° Cuenta Corriente Origen")

    # Beneficiario
    rut_beneficiario = models.CharField(max_length=12, verbose_name="RUT Beneficiario")
    nombre_beneficiario = models.CharField(max_length=200, verbose_name="Nombre Beneficiario")
    cuenta_destino = models.CharField(max_length=50, blank=True, null=True, verbose_name="Cuenta Bancaria Destino")

    fecha_pago = models.DateField(verbose_name="Fecha de Pago")
    glosa_contable = models.TextField(blank=True, null=True, verbose_name="Glosa Contable / Detalle")

    class Meta:
        verbose_name = "Egreso y Pago de Viático"
        verbose_name_plural = "Egresos y Pagos de Viáticos"
        unique_together = ('numero_egreso', 'ano_egreso', 'establecimiento')
        ordering = ["-ano_egreso", "-numero_egreso"]

    def __str__(self):
        return f"Egreso #{self.numero_egreso}/{self.ano_egreso} - $ {self.monto_total_pagado} ({self.nombre_beneficiario})"


class RendicionCometido(StandardModelEstablishment):
    """
    Rendición final de gastos y cuentas tras el regreso del funcionario.
    Controla diferencias a devolver por el funcionario o saldos a favor.
    """
    solicitud = models.OneToOneField('viaticos.SolicitudCometidoViatico', on_delete=models.PROTECT,
                                     related_name="rendicion_cuentas", verbose_name="Solicitud")
    fecha_rendicion = models.DateField(verbose_name="Fecha de Rendición")

    total_anticipo_recibido = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                                  verbose_name="Total Anticipo Recibido ($)")
    total_gastos_rendidos = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                                verbose_name="Total Gastos Justificados ($)")
    monto_a_devolver_institucion = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                                       verbose_name="Monto a Reintegrar por Funcionario ($)")
    monto_a_reembolsar_funcionario = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                                         verbose_name="Monto a Reembolsar al Funcionario ($)")

    informe_cometido_cumplido = models.TextField(verbose_name="Informe Ejecutivo de Actividades Cumplidas")
    rendicion_aprobada = models.BooleanField(default=False, verbose_name="¿Rendición Aprobada por Jefatura y Finanzas?")

    class Meta:
        verbose_name = "Rendición de Cometido y Cuentas"
        verbose_name_plural = "Rendiciones de Cometidos y Cuentas"
        ordering = ["-fecha_rendicion", "-id"]

    def __str__(self):
        return f"Rendición Solicitud #{self.solicitud.folio} - Aprobada: {self.rendicion_aprobada}"


class DetalleRendicionGasto(StandardModel):
    """
    Línea de detalle para boletas, facturas, peajes y respaldos adjuntos en la rendición.
    """
    rendicion = models.ForeignKey(RendicionCometido, on_delete=models.CASCADE, related_name="detalles_gasto",
                                  verbose_name="Rendición")
    tipo_documento = models.CharField(max_length=50, verbose_name="Tipo (Boleta / Factura / Ticket Peaje / Pasaje)")
    numero_documento = models.CharField(max_length=100, verbose_name="N° Documento")
    proveedor_razon_social = models.CharField(max_length=200, verbose_name="Razón Social / Proveedor")
    monto_documento = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto ($)")
    comprobante_digital = models.FileField(upload_to="viaticos/rendiciones/%Y/", blank=True, null=True,
                                           verbose_name="Imagen / PDF Comprobante")

    class Meta:
        verbose_name = "Detalle de Gasto Rendido"
        verbose_name_plural = "Detalles de Gastos Rendidos"
