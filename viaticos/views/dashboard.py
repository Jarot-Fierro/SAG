from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count
from django.utils import timezone
from django.views.generic import TemplateView

from ..models.finanzas import EgresoPagoViatico
from ..models.solicitud import SolicitudCometidoViatico
from ..models.transporte import GastoTransporte
from ..models.wokflow import AprobacionCometido


class ViaticosDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "viaticos/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_year = timezone.now().year

        solicitudes = SolicitudCometidoViatico.objects.filter(ano=current_year, is_active=True)
        if not self.request.user.is_superuser and hasattr(self.request.user, 'establecimiento'):
            solicitudes = solicitudes.filter(establecimiento=self.request.user.establecimiento)

        # Contadores principales
        total_solicitudes = solicitudes.count()
        pendientes_firma = solicitudes.filter(estado__in=[
            'ENVIADO_JEFATURA', 'EN_REVISION_SSGG', 'EN_REVISION_RRHH', 'RESOLUCION_EMITIDA', 'EN_PAGO'
        ]).count()
        pagados = solicitudes.filter(estado='PAGADO').count()
        rendidos = solicitudes.filter(estado='RENDIDO').count()
        urgentes = solicitudes.filter(es_urgente=True, estado__in=[
            'ENVIADO_JEFATURA', 'EN_REVISION_SSGG', 'EN_REVISION_RRHH'
        ]).count()

        # Montos financieros
        egresos = EgresoPagoViatico.objects.filter(ano_egreso=current_year, is_active=True)
        if not self.request.user.is_superuser and hasattr(self.request.user, 'establecimiento'):
            egresos = egresos.filter(establecimiento=self.request.user.establecimiento)

        total_pagado_viaticos = egresos.aggregate(Sum('monto_total_pagado'))['monto_total_pagado__sum'] or 0

        gastos_transporte = GastoTransporte.objects.filter(solicitud__ano=current_year, is_active=True)
        if not self.request.user.is_superuser and hasattr(self.request.user, 'establecimiento'):
            gastos_transporte = gastos_transporte.filter(solicitud__establecimiento=self.request.user.establecimiento)

        total_gastos_pasajes = gastos_transporte.aggregate(Sum('monto_real_ejecutado'))[
                                   'monto_real_ejecutado__sum'] or 0

        # Últimas solicitudes y aprobaciones
        ultimas_solicitudes = solicitudes.select_related('funcionario', 'unidad_organizacional').order_by('-id')[:5]
        ultimas_firmas = AprobacionCometido.objects.filter(
            solicitud__ano=current_year, is_active=True
        ).select_related('solicitud', 'usuario_firmante').order_by('-fecha_hora_accion')[:5]

        # Distribución por tipo de solicitud
        distribucion_tipos = solicitudes.values('tipo_solicitud').annotate(total=Count('id'))

        context.update({
            'current_year': current_year,
            'total_solicitudes': total_solicitudes,
            'pendientes_firma': pendientes_firma,
            'pagados': pagados,
            'rendidos': rendidos,
            'urgentes': urgentes,
            'total_pagado_viaticos': total_pagado_viaticos,
            'total_gastos_pasajes': total_gastos_pasajes,
            'ultimas_solicitudes': ultimas_solicitudes,
            'ultimas_firmas': ultimas_firmas,
            'distribucion_tipos': distribucion_tipos,
        })
        return context
