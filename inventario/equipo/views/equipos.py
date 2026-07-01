from core.mixin import DataTableMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from equipo.models.equipos import AsignacionIP


class EquiposIpListView(LoginRequiredMixin, DataTableMixin, TemplateView):
    template_name = 'equipo/list.html'
    model = AsignacionIP

    datatable_columns = [
        'ID',
        'IP',
        'Tipo Equipo',
        'Serie / Service Tag',
        'Marca',
        'Modelo',
        'Responsable',
        'Departamento',
        'Estado',
    ]

    datatable_order_fields = [
        'id',
        'ip__ip',
        'equipo__tipo_equipo',
        'equipo__serie',
        'equipo__marca__nombre',
        'equipo__modelo__nombre',
        'equipo__responsable__nombres',
        'equipo__departamento__nombre',
        'activa',
    ]

    datatable_search_fields = [
        'ip__ip__icontains',
        'equipo__serie__icontains',
        'equipo__marca__nombre__icontains',
        'equipo__modelo__nombre__icontains',
        'equipo__responsable__nombres__icontains',
        'equipo__departamento__nombre__icontains',
    ]

    def get_base_queryset(self):
        return AsignacionIP.objects.all().select_related(
            'ip',
            'ip__departamento',
            'equipo',
            'equipo__marca',
            'equipo__modelo',
            'equipo__responsable',
            'equipo__departamento',
        )

    def render_row(self, obj):
        ip_obj = obj.ip
        equipo = obj.equipo

        tipo = equipo.get_tipo_equipo_display() if equipo else '-'
        serie = equipo.serie if equipo else '-'
        marca = equipo.marca.nombre.upper() if equipo and equipo.marca else '-'
        modelo = equipo.modelo.nombre.upper() if equipo and equipo.modelo else '-'

        responsable = (
            f'<span class="badge rounded-pill bg-primary p-2">{equipo.responsable.nombres.upper()}</span>'
            if equipo and equipo.responsable
            else '<span class="badge rounded-pill bg-secondary">SIN RESPONSABLE</span>'
        )

        departamento = '-'
        if equipo and equipo.departamento:
            departamento = equipo.departamento.nombre.upper()
        elif ip_obj and ip_obj.departamento:
            departamento = ip_obj.departamento.nombre.upper()

        # Determinamos el estado según el check 'activa' y si tiene equipo asociado
        if obj.activa and equipo:
            estado_html = '<span class="badge bg-danger">ASIGNADA</span>'
            ip_html = f'<span class="badge bg-danger p-2">{ip_obj.ip}</span>'
        else:
            estado_html = '<span class="badge bg-success">LIBRE</span>'
            ip_html = f'<span class="badge bg-success p-2">{ip_obj.ip}</span>'

        return {
            'ID': obj.id,
            'IP': ip_html,
            'Tipo Equipo': tipo,
            'Serie / Service Tag': serie,
            'Marca': marca,
            'Modelo': modelo,
            'Responsable': responsable,
            'Departamento': departamento,
            'Estado': estado_html,
        }

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('datatable'):
            return self.get_datatable_response(request)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Listado de IPs y Equipos (Asignaciones)',
            'list_url': reverse_lazy('list_equipos_ip'),
            'datatable_enabled': True,
            'datatable_order': [[0, 'desc']],
            'datatable_page_length': 100,
            'columns': self.datatable_columns,
        })
        return context
