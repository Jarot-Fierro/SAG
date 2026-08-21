from django.db import models

from core.standard.models import StandardModel, StandardModelEstablishment


class LugarDestino(StandardModelEstablishment):
    """
    Catálogo centralizado de destinos, comunas, localidades o zonas de comisión.
    Reemplaza la tabla SIALUGAR y campos de texto libre.
    """
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código de Lugar")
    nombre = models.CharField(max_length=255, verbose_name="Nombre / Ciudad / Localidad")
    region = models.CharField(max_length=100, default="Coquimbo", verbose_name="Región")
    comuna = models.CharField(max_length=100, blank=True, null=True, verbose_name="Comuna")
    descripcion_adicional = models.TextField(blank=True, null=True, verbose_name="Detalle de Ubicación")
    es_rural_dificil_acceso = models.BooleanField(default=False, verbose_name="¿Zona rural / difícil acceso?")
    distancia_km_referencial = models.PositiveIntegerField(default=0, verbose_name="Distancia ref. (KM)")

    UPPERCASE_FIELDS = ['codigo', 'nombre', 'region', 'comuna']

    class Meta:
        verbose_name = "Lugar de Destino"
        verbose_name_plural = "Lugares de Destino"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.comuna or self.region})"


class EscalaViatico(StandardModel):
    """
    Matriz de valores y tarifas legales de viáticos según estamento, grado y año.
    Permite parametrizar montos de 100% (pernocta), 50% (parcial) y faena.
    """
    ano_vigencia = models.PositiveIntegerField(verbose_name="Año de Vigencia")
    grado_desde = models.CharField(max_length=2, verbose_name="Grado Desde")
    grado_hasta = models.CharField(max_length=2, verbose_name="Grado Hasta")
    estamento = models.CharField(max_length=100, blank=True, null=True, verbose_name="Estamento / Ley")

    valor_100_pernocta = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor 100% Pernocta ($)")
    valor_50_parcial = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor 50% Alimentación ($)")
    valor_faena = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor Faena ($)")
    observacion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observaciones")

    class Meta:
        verbose_name = "Escala de Viático"
        verbose_name_plural = "Escalas de Viáticos"
        ordering = ["-ano_vigencia", "grado_desde"]

    def __str__(self):
        return f"Año {self.ano_vigencia} - Grados {self.grado_desde} a {self.grado_hasta} ($ {self.valor_100_pernocta})"


class VistoLegal(StandardModelEstablishment):
    """
    Catálogo de considerandos y 'Vistos' jurídicos para resoluciones y decretos exentos.
    Reemplaza la tabla SIAVISTOS.
    """
    codigo = models.CharField(max_length=50, verbose_name="Código / Referencia")
    texto_visto = models.TextField(verbose_name="Texto del Visto Legal")
    corresponde_a = models.CharField(max_length=100, blank=True, null=True,
                                     verbose_name="Tipo (Cometido/Viático/Ambos)")
    orden = models.PositiveIntegerField(default=1, verbose_name="Orden de Aparición")

    class Meta:
        verbose_name = "Visto Legal"
        verbose_name_plural = "Vistos Legales"
        ordering = ["orden", "codigo"]

    def __str__(self):
        return f"{self.codigo} - {self.texto_visto[:80]}..."
