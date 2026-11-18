from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.standard.views import StandardCreateView, StandardUpdateView
from ..forms.productos import FormProducto
from ..models.productos import Producto


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class ProductoListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventario_tic/productos_list.html'
    columns = (
        'nombre', 'tipo_producto__nombre', 'marca__nombre', 'modelo__nombre',
        'stock_total', 'stock_disponible', 'stock_minimo', 'descripcion',
    )

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse({'error': 'Acción no válida'}, status=400)
        draw = max(0, _as_int(request.POST.get('draw'), 1))
        start = max(0, _as_int(request.POST.get('start'), 0))
        length = _as_int(request.POST.get('length'), 10)
        if length < 1 and length != -1:
            length = 10

        queryset = Producto.objects.filter(is_active=True)
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
            for field in ('nombre', 'tipo_producto__nombre', 'marca__nombre', 'modelo__nombre', 'descripcion'):
                filters |= Q(**{f'{field}__icontains': search})
            if search.isdigit():
                for field in ('stock_total', 'stock_disponible', 'stock_minimo'):
                    filters |= Q(**{field: int(search)})
            queryset = queryset.filter(filters)
        records_filtered = queryset.count()
        index = _as_int(request.POST.get('order[0][column]'), 0)
        field = self.columns[index] if 0 <= index < len(self.columns) else 'nombre'
        if request.POST.get('order[0][dir]') == 'desc':
            field = f'-{field}'
        queryset = queryset.order_by(field, 'pk')
        if length != -1:
            queryset = queryset[start:start + length]
        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': list(queryset.values('id', *self.columns)),
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Productos'
        context['edit_url_template'] = reverse_lazy('inventario_tic:producto_update', kwargs={'pk': 0})
        context['delete_url_template'] = reverse_lazy('inventario_tic:producto_eliminar', kwargs={'pk': 0})
        return context


class ProductoCreateView(StandardCreateView):
    template_name = 'inventario_tic/productos_form.html'
    model = Producto
    form_class = FormProducto
    title = 'Nuevo Producto'
    success_url = reverse_lazy('inventario_tic:producto_create')

    def get_list_url(self):
        return reverse_lazy('inventario_tic:producto_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context


class ProductoUpdateView(StandardUpdateView):
    template_name = 'inventario_tic/productos_form.html'
    model = Producto
    form_class = FormProducto
    title = 'Actualizar Producto'
    success_url = reverse_lazy('inventario_tic:producto_create')

    def get_queryset(self):
        queryset = Producto.objects.filter(is_active=True)
        if not self.request.user.is_superuser:
            queryset = queryset.filter(establecimiento_id=self.request.user.establecimiento_id)
        return queryset

    def get_list_url(self):
        return reverse_lazy('inventario_tic:producto_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context


@login_required
@require_POST
def producto_eliminar(request, pk):
    queryset = Producto.objects.all()

    if not request.user.is_superuser:
        queryset = queryset.filter(
            establecimiento_id=request.user.establecimiento_id
        )

    producto = get_object_or_404(queryset, pk=pk)
    nombre = producto.nombre

    try:
        producto.is_active = False

        if hasattr(producto, 'updated_by'):
            producto.updated_by = request.user

        producto.save()

        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': (
                f'El producto "{nombre}" (ID: {pk}) '
                'fue desactivado correctamente.'
            ),
        })
    except Exception:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': 'Ocurrió un error al intentar desactivar el producto.',
        }, status=400)
