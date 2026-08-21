from django.db import models

from core.standard.models import StandardModelEstablishment


class ValidacionRelojControl(StandardModelEstablishment):
    """
    Validación de concordancia entre los días del cometido y los registros del reloj control.
    Reemplaza SIACORTERELOJCONTROL.
    """
    funcionario = models.ForeignKey('core.Funcionario', on_delete=models.PROTECT,
                                    related_name="validaciones_asistencia", verbose_name="Funcionario")
    solicitud = models.ForeignKey('viaticos.SolicitudCometidoViatico', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="validaciones_reloj", verbose_name="Cometido Asociado")

    fecha_inicio_ausencia = models.DateField(verbose_name="Fecha Inicio")
    fecha_termino_ausencia = models.DateField(verbose_name="Fecha Término")
    tipo_ausentismo = models.CharField(max_length=100, default="COMETIDO_FUNCIONAL",
                                       verbose_name="Tipo de Justificación de Asistencia")
    dias_justificados = models.PositiveIntegerField(verbose_name="Cantidad de Días")

    sincronizado_reloj = models.BooleanField(default=False, verbose_name="¿Sincronizado con Reloj Control?")
    observacion_corte = models.TextField(blank=True, null=True, verbose_name="Observaciones de Asistencia")

    class Meta:
        verbose_name = "Corte de Asistencia / Reloj Control"
        verbose_name_plural = "Cortes de Asistencia / Reloj Control"
        ordering = ["-fecha_inicio_ausencia", "-id"]


class PermisoGremial(StandardModelEstablishment):
    """
    Registro y control de permisos gremiales y su compatibilidad con viáticos.
    Reemplaza SIAPERMISOGREMIAL.
    """
    folio_gremial = models.PositiveIntegerField(verbose_name="N° Folio Permiso Gremial")
    ano = models.PositiveIntegerField(verbose_name="Año")
    funcionario = models.ForeignKey('core.Funcionario', on_delete=models.PROTECT, related_name="permisos_gremiales",
                                    verbose_name="Dirigente / Funcionario")
    cargo_en_gremio = models.CharField(max_length=150, verbose_name="Cargo en la Asociación / Gremio")

    lugar_actividad = models.ForeignKey('viaticos.LugarDestino', on_delete=models.PROTECT,
                                        related_name="permisos_gremiales", verbose_name="Lugar Actividad")
    motivo = models.TextField(verbose_name="Motivo de la Actividad Gremial")
    fecha_desde = models.DateField(verbose_name="Desde")
    fecha_hasta = models.DateField(verbose_name="Hasta")

    aprobado = models.BooleanField(default=False, verbose_name="¿Aprobado por Autoridad?")
    aprobado_por = models.ForeignKey('core.Funcionario', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="permisos_gremiales_aprobados", verbose_name="Aprobador")

    class Meta:
        verbose_name = "Permiso Gremial"
        verbose_name_plural = "Permisos Gremiales"
        unique_together = ('folio_gremial', 'ano', 'establecimiento')
