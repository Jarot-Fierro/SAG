from django.db import models

from core.standard.models import StandardModelEstablishment


class ResolucionCometido(StandardModelEstablishment):
    """
    Formalización administrativa del cometido mediante Decreto / Resolución Exenta.
    Reemplaza la lógica dispersa de SIAVISTOS y SIAFIRMANTESDESP.
    """
    solicitud = models.OneToOneField('viaticos.SolicitudCometidoViatico', on_delete=models.PROTECT,
                                     related_name="resolucion_formal", verbose_name="Solicitud")
    numero_resolucion = models.PositiveIntegerField(verbose_name="N° Resolución Exenta")
    ano_resolucion = models.PositiveIntegerField(verbose_name="Año Resolución")
    fecha_emision = models.DateField(verbose_name="Fecha de Emisión")

    vistos = models.ManyToManyField('viaticos.VistoLegal', related_name="resoluciones",
                                    verbose_name="Vistos Legales Aplicados")
    considerandos = models.TextField(verbose_name="Considerandos Específicos")
    texto_resuelve = models.TextField(verbose_name="Cuerpo del Resuelve")

    firmante_nombre = models.CharField(max_length=200, verbose_name="Nombre Firmante Legal")
    firmante_cargo = models.CharField(max_length=200, verbose_name="Cargo Firmante Legal")

    documento_pdf_firmado = models.FileField(upload_to="viaticos/resoluciones/%Y/", blank=True, null=True,
                                             verbose_name="PDF Resolución Firmada")

    class Meta:
        verbose_name = "Resolución Exenta de Cometido"
        verbose_name_plural = "Resoluciones Exentas de Cometidos"
        unique_together = ('numero_resolucion', 'ano_resolucion', 'establecimiento')
        ordering = ['-ano_resolucion', '-numero_resolucion']

    def __str__(self):
        return f"Res. Exenta N° {self.numero_resolucion}/{self.ano_resolucion} - Solicitud #{self.solicitud.folio}"
