import json
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from ..models.catalogo import Ips
from ..models.tipo_activo import TipoActivo
from ..models.activo import Activo

class DashboardGestionTicView(LoginRequiredMixin, TemplateView):
    template_name = 'gestion_tic/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        establecimiento = self.request.user.establecimiento

        # Resumen de IPs
        ips_query = Ips.objects.filter(establecimiento=establecimiento, is_active=True)
        ips_disponibles = ips_query.filter(asignado=False).count()
        ips_asignadas = ips_query.filter(asignado=True).count()

        # Segmentos de IPs
        segmentos = set()
        for ip in ips_query.values_list('ip', flat=True):
            parts = ip.split('.')
            if len(parts) == 4:
                segmentos.add(".".join(parts[:3]) + ".x")
        
        segmentos_lista = sorted(list(segmentos))
        segmentos_total = len(segmentos_lista)

        # Resumen de Tipos de Activos
        tipos_activos_total = TipoActivo.objects.filter(establecimiento=establecimiento, is_active=True).count()

        # Resumen de Equipos por Tipo de Activo
        activos_por_tipo = list(Activo.objects.filter(
            establecimiento=establecimiento, 
            is_active=True
        ).values('tipo__nombre').annotate(total=Count('id')).order_by('-total'))

        context.update({
            'title': 'Dashboard Gestión TIC',
            'ips_disponibles': ips_disponibles,
            'ips_asignadas': ips_asignadas,
            'segmentos_total': segmentos_total,
            'segmentos_lista': segmentos_lista,
            'tipos_activos_total': tipos_activos_total,
            'activos_por_tipo': activos_por_tipo,
            'activos_por_tipo_json': json.dumps(activos_por_tipo),
        })
        return context
