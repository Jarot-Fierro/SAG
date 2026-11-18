from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.standard.views import StandardCreateView, StandardUpdateView
from ..forms.impresora import FormImpresora
from ..models.impresoras import Impresora


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def puede_generar_acta_impresora(departamento_nombre, establecimiento_nombre):
    return bool((departamento_nombre or '').strip() and (establecimiento_nombre or '').strip())


class ImpresoraListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventario_tic/impresoras_list.html'
    columns = (
        'numero_serie', 'hh', 'marca__nombre', 'modelo__nombre',
        'imprime_color', 'tiene_ethernet', 'tiene_wifi', 'toner', 'departamento__nombre', 'observacion',
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse({'error': 'Acción no válida'}, status=400)
        draw = max(0, _as_int(request.POST.get('draw'), 1))
        start = max(0, _as_int(request.POST.get('start'), 0))
        length = _as_int(request.POST.get('length'), 10)
        if length < 1 and length != -1:
            length = 10

        queryset = Impresora.objects.filter(is_active=True)
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
                if field not in ('imprime_color', 'tiene_ethernet', 'tiene_wifi'):
                    filters |= Q(**{f'{field}__icontains': search})
            queryset = queryset.filter(filters)
        records_filtered = queryset.count()
        index = _as_int(request.POST.get('order[0][column]'), 0)
        field = self.columns[index] if 0 <= index < len(self.columns) else 'numero_serie'
        if request.POST.get('order[0][dir]') == 'desc':
            field = f'-{field}'
        queryset = queryset.order_by(field, 'pk')
        if length != -1:
            queryset = queryset[start:start + length]
        data = list(queryset.values('id', 'establecimiento__nombre', *self.columns))
        for row in data:
            row['puede_generar_acta'] = puede_generar_acta_impresora(
                row['departamento__nombre'], row['establecimiento__nombre'],
            )
        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['acta_url_template'] = reverse_lazy('inventario_tic:generar_acta_impresoras', kwargs={'pk': 0})
        context['title'] = 'Listado de Impresoras'
        context['edit_url_template'] = reverse_lazy('inventario_tic:impresora_update', kwargs={'pk': 0})
        context['delete_url_template'] = reverse_lazy('inventario_tic:impresora_eliminar', kwargs={'pk': 0})
        return context


class ImpresoraCreateView(StandardCreateView):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    template_name = 'inventario_tic/impresoras_form.html'
    model = Impresora
    form_class = FormImpresora
    title = 'Nueva Impresora'
    success_url = reverse_lazy('inventario_tic:impresora_create')

    def get_list_url(self):
        return reverse_lazy('inventario_tic:impresora_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context


class ImpresoraUpdateView(StandardUpdateView):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    template_name = 'inventario_tic/impresoras_form.html'
    model = Impresora
    form_class = FormImpresora
    title = 'Actualizar Impresora'
    success_url = reverse_lazy('inventario_tic:impresora_create')

    def get_queryset(self):
        queryset = Impresora.objects.filter(is_active=True)
        if not self.request.user.is_superuser:
            queryset = queryset.filter(establecimiento_id=self.request.user.establecimiento_id)
        return queryset

    def get_list_url(self):
        return reverse_lazy('inventario_tic:impresora_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context


@login_required
@require_POST
def impresora_eliminar(request, pk):
    queryset = Impresora.objects.all()

    if not request.user.is_superuser:
        queryset = queryset.filter(
            establecimiento_id=request.user.establecimiento_id
        )

    impresora = get_object_or_404(queryset, pk=pk)
    nombre = impresora.numero_serie

    try:
        impresora.is_active = False

        if hasattr(impresora, 'updated_by'):
            impresora.updated_by = request.user

        impresora.save()

        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': (
                f'La impresora "{nombre}" (ID: {pk}) '
                'fue desactivada correctamente.'
            ),
        })
    except Exception:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': 'Ocurrió un error al intentar desactivar el impresora.',
        }, status=400)
