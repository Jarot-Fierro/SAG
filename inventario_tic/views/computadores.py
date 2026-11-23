from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.standard.views import StandardCreateView, StandardUpdateView
from ..forms.computadores import FormComputador, FormRecepcionComputador
from ..models.computadores import Computador
from ..forms.mantenedores import FormFuncionarioInventario


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def puede_generar_acta_computador(responsable, establecimiento_nombre):
    return bool((responsable or '').strip() and (establecimiento_nombre or '').strip())


class ComputadorListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventario_tic/computadores_list.html'
    columns = (
        'codigo_inventario', 'numero_serie', 'marca__nombre', 'modelo__nombre',
        'formato', 'procesador', 'memoria_ram_gb', 'almacenamiento',
        'tarjeta_grafica', 'observacion', 'establecimiento_mantenedor__nombre', 'responsable__nombre',
    )

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse({'error': 'Acción no válida'}, status=400)
        draw = max(0, _as_int(request.POST.get('draw'), 1))
        start = max(0, _as_int(request.POST.get('start'), 0))
        length = _as_int(request.POST.get('length'), 10)
        if length < 1 and length != -1:
            length = 10

        queryset = Computador.objects.filter(is_active=True)
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
                filters |= Q(**{f'{field}__icontains': search})
            for value, label in Computador.Formato.choices:
                if search.casefold() in label.casefold():
                    filters |= Q(formato=value)
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
            row['responsable'] = row.pop('responsable__nombre')
            row['puede_generar_acta'] = puede_generar_acta_computador(
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
        context['acta_url_template'] = reverse_lazy('inventario_tic:generar_acta_computadores', kwargs={'pk': 0})
        context['recepcion_url_template'] = reverse_lazy('inventario_tic:computador_recepcion_update', kwargs={'pk': 0})
        context['devolucion_url_template'] = reverse_lazy('inventario_tic:computador_devolucion', kwargs={'pk': 0})
        context['title'] = 'Listado de Computadores'
        context['edit_url_template'] = reverse_lazy('inventario_tic:computador_update', kwargs={'pk': 0})
        context['delete_url_template'] = reverse_lazy('inventario_tic:computador_eliminar', kwargs={'pk': 0})
        return context


class ComputadorCreateView(StandardCreateView):
    template_name = 'inventario_tic/computadores_form.html'
    model = Computador
    form_class = FormComputador
    title = 'Nuevo Computador'
    success_url = reverse_lazy('inventario_tic:computador_list')

    def get_list_url(self):
        return reverse_lazy('inventario_tic:computador_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context


class ComputadorUpdateView(StandardUpdateView):
    template_name = 'inventario_tic/computadores_form.html'
    model = Computador
    form_class = FormComputador
    title = 'Actualizar Computador'
    success_url = reverse_lazy('inventario_tic:computador_list')

    def get_queryset(self):
        queryset = Computador.objects.filter(is_active=True)
        if not self.request.user.is_superuser:
            establecimiento_id = getattr(self.request.user, 'establecimiento_id', None)
            queryset = queryset.filter(establecimiento_id=establecimiento_id) if establecimiento_id else queryset.none()
        return queryset

    def get_list_url(self):
        return reverse_lazy('inventario_tic:computador_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context


class ComputadorRecepcionUpdateView(StandardUpdateView):
    template_name = 'inventario_tic/computadores_form.html'
    model = Computador
    form_class = FormRecepcionComputador
    success_url = reverse_lazy('inventario_tic:computador_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.asignado = True
        return super().form_valid(form)

    def get_queryset(self):
        queryset = Computador.objects.filter(is_active=True)
        if not self.request.user.is_superuser:
            establecimiento_id = getattr(self.request.user, 'establecimiento_id', None)
            queryset = queryset.filter(establecimiento_id=establecimiento_id) if establecimiento_id else queryset.none()
        return queryset

    def get_list_url(self):
        return reverse_lazy('inventario_tic:computador_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_heading'] = 'Datos de recepción'
        context['submit_label'] = 'Guardar recepción'
        context['title'] = f'Recepción de Computador: {self.object}'
        context['funcionario_form'] = FormFuncionarioInventario()
        context['last_form'] = True
        return context


@login_required
@require_POST
def computador_devolucion(request, pk):
    queryset = Computador.objects.filter(is_active=True)
    if not request.user.is_superuser:
        establecimiento_id = getattr(request.user, 'establecimiento_id', None)
        queryset = queryset.filter(establecimiento_id=establecimiento_id) if establecimiento_id else queryset.none()
    computador = get_object_or_404(queryset, pk=pk)
    if not computador.asignado:
        return JsonResponse({'success': False, 'message': 'El computador no está asignado.'}, status=400)
    computador.responsable = None
    computador.establecimiento_mantenedor = None
    computador.jefe_entrega = None
    computador.asignado = False
    computador.updated_by = request.user
    computador.save(update_fields=[
        'responsable', 'establecimiento_mantenedor', 'jefe_entrega',
        'asignado', 'updated_by', 'updated_at',
    ])
    return JsonResponse({'success': True, 'message': 'Devolución registrada correctamente.'})


@login_required
@require_POST
def computador_eliminar(request, pk):
    queryset = Computador.objects.all()

    if not request.user.is_superuser:
        establecimiento_id = getattr(request.user, 'establecimiento_id', None)
        queryset = queryset.filter(establecimiento_id=establecimiento_id) if establecimiento_id else queryset.none()

    computador = get_object_or_404(queryset, pk=pk)
    nombre = computador.codigo_inventario or computador.numero_serie

    try:
        computador.is_active = False

        if hasattr(computador, 'updated_by'):
            computador.updated_by = request.user

        computador.save()

        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': (
                f'El computador "{nombre}" (ID: {pk}) '
                'fue desactivado correctamente.'
            ),
        })
    except Exception:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': 'Ocurrió un error al intentar desactivar el computador.',
        }, status=400)
