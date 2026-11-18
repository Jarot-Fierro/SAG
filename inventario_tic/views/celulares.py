from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.standard.views import StandardCreateView, StandardUpdateView
from ..forms.celulares import FormCelular, FormRecepcionCelular
from ..forms.mantenedores import FormFuncionarioInventario
from ..models.celulares import Celular


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def puede_generar_acta_celular(responsable, establecimiento_nombre):
    return bool((responsable or '').strip() and (establecimiento_nombre or '').strip())


class CelularListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventario_tic/celulares_list.html'
    columns = (
        'imei', 'numero_telefono', 'marca__nombre', 'modelo__nombre',
        'propietario__nombre', 'minsal', 'establecimiento_mantenedor__nombre', 'responsable__nombre', 'numero_chip',
        'minutos',
    )

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse({'error': 'Acción no válida'}, status=400)
        draw = max(0, _as_int(request.POST.get('draw'), 1))
        start = max(0, _as_int(request.POST.get('start'), 0))
        length = _as_int(request.POST.get('length'), 10)
        if length < 1 and length != -1:
            length = 10

        queryset = Celular.objects.filter(is_active=True)
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
                if field != 'minsal':
                    filters |= Q(**{f'{field}__icontains': search})
            if search.casefold() in ('sí', 'si', 'no'):
                filters |= Q(minsal=search.casefold() != 'no')
            queryset = queryset.filter(filters)
        records_filtered = queryset.count()
        index = _as_int(request.POST.get('order[0][column]'), 0)
        field = self.columns[index] if 0 <= index < len(self.columns) else 'imei'
        if request.POST.get('order[0][dir]') == 'desc':
            field = f'-{field}'
        queryset = queryset.order_by(field, 'pk')
        if length != -1:
            queryset = queryset[start:start + length]
        data = list(queryset.values('id', 'asignado', *self.columns))
        for row in data:
            row['responsable'] = row.pop('responsable__nombre')
            row['puede_generar_acta'] = puede_generar_acta_celular(
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
        context['devolucion_url_template'] = reverse_lazy('inventario_tic:celular_devolucion', kwargs={'pk': 0})
        context['recepcion_url_template'] = reverse_lazy('inventario_tic:celular_recepcion_update', kwargs={'pk': 0})
        context['acta_url_template'] = reverse_lazy('inventario_tic:generar_acta_celulares', kwargs={'pk': 0})
        context['title'] = 'Listado de Celulares'
        context['edit_url_template'] = reverse_lazy('inventario_tic:celular_update', kwargs={'pk': 0})
        context['delete_url_template'] = reverse_lazy('inventario_tic:celular_eliminar', kwargs={'pk': 0})
        return context


class CelularCreateView(StandardCreateView):
    template_name = 'inventario_tic/celulares_form.html'
    model = Celular
    form_class = FormCelular
    title = 'Nuevo Celular'
    success_url = reverse_lazy('inventario_tic:celular_create')

    def get_list_url(self):
        return reverse_lazy('inventario_tic:celular_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context


class CelularUpdateView(StandardUpdateView):
    template_name = 'inventario_tic/celulares_form.html'
    model = Celular
    form_class = FormCelular
    title = 'Actualizar Celular'
    success_url = reverse_lazy('inventario_tic:celular_create')

    def get_queryset(self):
        queryset = Celular.objects.filter(is_active=True)
        if not self.request.user.is_superuser:
            queryset = queryset.filter(establecimiento_id=self.request.user.establecimiento_id)
        return queryset

    def get_list_url(self):
        return reverse_lazy('inventario_tic:celular_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context


class CelularRecepcionUpdateView(StandardUpdateView):
    template_name = 'inventario_tic/celulares_form.html'
    model = Celular
    form_class = FormRecepcionCelular
    success_url = reverse_lazy('inventario_tic:celular_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.asignado = True
        return super().form_valid(form)

    def get_queryset(self):
        queryset = Celular.objects.filter(is_active=True)
        if not self.request.user.is_superuser:
            establecimiento_id = getattr(self.request.user, 'establecimiento_id', None)
            queryset = queryset.filter(establecimiento_id=establecimiento_id) if establecimiento_id else queryset.none()
        return queryset

    def get_list_url(self):
        return reverse_lazy('inventario_tic:celular_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_heading'] = 'Datos de recepción'
        context['submit_label'] = 'Guardar recepción'
        context['title'] = f'Recepción de Celular: {self.object}'
        context['funcionario_form'] = FormFuncionarioInventario()
        context['last_form'] = True
        return context


@login_required
@require_POST
def celular_devolucion(request, pk):
    queryset = Celular.objects.filter(is_active=True)
    if not request.user.is_superuser:
        establecimiento_id = getattr(request.user, 'establecimiento_id', None)
        queryset = queryset.filter(establecimiento_id=establecimiento_id) if establecimiento_id else queryset.none()
    celular = get_object_or_404(queryset, pk=pk)
    if not celular.asignado:
        return JsonResponse({'success': False, 'message': 'El celular no está asignado.'}, status=400)
    celular.responsable = None
    celular.establecimiento_mantenedor = None
    celular.jefe_entrega = None
    celular.asignado = False
    celular.updated_by = request.user
    celular.save(update_fields=[
        'responsable', 'establecimiento_mantenedor', 'jefe_entrega',
        'asignado', 'updated_by', 'updated_at',
    ])
    return JsonResponse({'success': True, 'message': 'Devolución registrada correctamente.'})


@login_required
@require_POST
def celular_eliminar(request, pk):
    queryset = Celular.objects.all()

    if not request.user.is_superuser:
        queryset = queryset.filter(
            establecimiento_id=request.user.establecimiento_id
        )

    celular = get_object_or_404(queryset, pk=pk)
    nombre = f"{celular.marca.nombre if celular.marca else ''} {celular.modelo.nombre if celular.modelo else ''} - {celular.imei}".strip()
    if not nombre or nombre == '-':
        nombre = celular.imei or f'Celular #{celular.pk}'

    try:
        celular.is_active = False

        if hasattr(celular, 'updated_by'):
            celular.updated_by = request.user

        celular.save()

        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': (
                f'El celular "{nombre}" (ID: {pk}) '
                'fue desactivado correctamente.'
            ),
        })
    except Exception:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': 'Ocurrió un error al intentar desactivar el celular.',
        }, status=400)
