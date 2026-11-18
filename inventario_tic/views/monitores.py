from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.standard.views import StandardCreateView, StandardUpdateView
from ..forms.monitores import FormMonitor, FormRecepcionMonitor
from ..models.monitores import Monitor


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def puede_generar_acta_monitor(responsable, establecimiento_nombre):
    return bool((responsable or '').strip() and (establecimiento_nombre or '').strip())


class MonitorListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventario_tic/monitores_list.html'
    columns = (
        'codigo_inventario', 'numero_serie', 'marca__nombre', 'modelo__nombre',
        'pulgadas', 'resolucion', 'frecuencia_hz', 'tiene_hdmi', 'tiene_vga',
        'establecimiento_mantenedor__nombre', 'responsable',
    )

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse({'error': 'Acción no válida'}, status=400)
        draw = max(0, _as_int(request.POST.get('draw'), 1))
        start = max(0, _as_int(request.POST.get('start'), 0))
        length = _as_int(request.POST.get('length'), 10)
        if length < 1 and length != -1:
            length = 10

        queryset = Monitor.objects.filter(is_active=True)
        if not request.user.is_superuser:
            establecimiento_id = getattr(request.user, 'establecimiento_id', None)
            if establecimiento_id:
                queryset = queryset.filter(establecimiento_id=establecimiento_id)
            else:
                queryset = queryset.none()
        records_total = queryset.count()
        search = request.POST.get('search[value]', '').strip()
        if search:
            filters = Q()
            for field in self.columns:
                if field not in ('tiene_hdmi', 'tiene_vga'):
                    filters |= Q(**{f'{field}__icontains': search})
            if search.casefold() in ('sí', 'si', 'no'):
                for field in ('tiene_hdmi', 'tiene_vga'):
                    filters |= Q(**{field: search.casefold() != 'no'})
            queryset = queryset.filter(filters)
        records_filtered = queryset.count()
        index = _as_int(request.POST.get('order[0][column]'), 0)
        field = self.columns[index] if 0 <= index < len(self.columns) else 'codigo_inventario'
        if request.POST.get('order[0][dir]') == 'desc':
            field = f'-{field}'
        queryset = queryset.order_by(field, 'pk')
        if length != -1:
            queryset = queryset[start:start + length]
        data = list(queryset.values('id', 'asignado', *self.columns))
        for row in data:
            row['puede_generar_acta'] = puede_generar_acta_monitor(
                row['responsable'], row['establecimiento_mantenedor__nombre'],
            )
        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['acta_url_template'] = reverse_lazy('inventario_tic:generar_acta_monitores', kwargs={'pk': 0})
        context['recepcion_url_template'] = reverse_lazy('inventario_tic:monitor_recepcion_update', kwargs={'pk': 0})
        context['devolucion_url_template'] = reverse_lazy('inventario_tic:monitor_devolucion', kwargs={'pk': 0})
        context['title'] = 'Listado de Monitores'
        context['edit_url_template'] = reverse_lazy('inventario_tic:monitor_update', kwargs={'pk': 0})
        context['delete_url_template'] = reverse_lazy('inventario_tic:monitor_eliminar', kwargs={'pk': 0})
        return context


class MonitorCreateView(StandardCreateView):
    template_name = 'inventario_tic/monitores_form.html'
    model = Monitor
    form_class = FormMonitor
    title = 'Nuevo Monitor'
    success_url = reverse_lazy('inventario_tic:monitor_create')

    def get_list_url(self):
        return reverse_lazy('inventario_tic:monitor_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context


class MonitorUpdateView(StandardUpdateView):
    template_name = 'inventario_tic/monitores_form.html'
    model = Monitor
    form_class = FormMonitor
    title = 'Actualizar Monitor'
    success_url = reverse_lazy('inventario_tic:monitor_create')

    def get_queryset(self):
        queryset = Monitor.objects.filter(is_active=True)
        if not self.request.user.is_superuser:
            establecimiento_id = getattr(self.request.user, 'establecimiento_id', None)
            queryset = queryset.filter(establecimiento_id=establecimiento_id) if establecimiento_id else queryset.none()
        return queryset

    def get_list_url(self):
        return reverse_lazy('inventario_tic:monitor_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context


class MonitorRecepcionUpdateView(StandardUpdateView):
    template_name = 'inventario_tic/monitores_form.html'
    model = Monitor
    form_class = FormRecepcionMonitor
    success_url = reverse_lazy('inventario_tic:monitor_list')

    def form_valid(self, form):
        form.instance.asignado = True
        return super().form_valid(form)

    def get_queryset(self):
        queryset = Monitor.objects.filter(is_active=True)
        if not self.request.user.is_superuser:
            establecimiento_id = getattr(self.request.user, 'establecimiento_id', None)
            queryset = queryset.filter(establecimiento_id=establecimiento_id) if establecimiento_id else queryset.none()
        return queryset

    def get_list_url(self):
        return reverse_lazy('inventario_tic:monitor_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_heading'] = 'Datos de recepción'
        context['submit_label'] = 'Guardar recepción'
        context['title'] = f'Recepción de Monitor: {self.object}'
        context['last_form'] = True
        return context


@login_required
@require_POST
def monitor_devolucion(request, pk):
    queryset = Monitor.objects.filter(is_active=True)
    if not request.user.is_superuser:
        establecimiento_id = getattr(request.user, 'establecimiento_id', None)
        queryset = queryset.filter(establecimiento_id=establecimiento_id) if establecimiento_id else queryset.none()
    monitor = get_object_or_404(queryset, pk=pk)
    if not monitor.asignado:
        return JsonResponse({'success': False, 'message': 'El monitor no está asignado.'}, status=400)
    monitor.responsable = None
    monitor.establecimiento_mantenedor = None
    monitor.jefe_entrega = None
    monitor.asignado = False
    monitor.updated_by = request.user
    monitor.save(update_fields=[
        'responsable', 'establecimiento_mantenedor', 'jefe_entrega',
        'asignado', 'updated_by', 'updated_at',
    ])
    return JsonResponse({'success': True, 'message': 'Devolución registrada correctamente.'})


@login_required
@require_POST
def monitor_eliminar(request, pk):
    queryset = Monitor.objects.all()

    if not request.user.is_superuser:
        establecimiento_id = getattr(request.user, 'establecimiento_id', None)
        queryset = queryset.filter(establecimiento_id=establecimiento_id) if establecimiento_id else queryset.none()

    monitor = get_object_or_404(queryset, pk=pk)
    nombre = monitor.codigo_inventario or monitor.numero_serie

    try:
        monitor.is_active = False

        if hasattr(monitor, 'updated_by'):
            monitor.updated_by = request.user

        monitor.save()

        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': (
                f'El monitor "{nombre}" (ID: {pk}) '
                'fue desactivado correctamente.'
            ),
        })
    except Exception:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': 'Ocurrió un error al intentar desactivar el monitor.',
        }, status=400)
