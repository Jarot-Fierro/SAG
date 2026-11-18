from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.standard.views import StandardCreateView, StandardUpdateView
from ..forms.mantenedores import FormFuncionarioInventario
from ..models.mantenedores import FuncionarioInventario


def funcionarios_visibles(user):
    queryset = FuncionarioInventario.objects.filter(is_active=True)
    if not user.is_superuser:
        establecimiento_id = getattr(user, 'establecimiento_id', None)
        queryset = queryset.filter(establecimiento_id=establecimiento_id) if establecimiento_id else queryset.none()
    return queryset


def _numero(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class FuncionarioInventarioListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventario_tic/funcionarios_list.html'

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse({'error': 'Acción no válida'}, status=400)
        queryset = funcionarios_visibles(request.user)
        total = queryset.count()
        search = request.POST.get('search[value]', '').strip()
        if search:
            queryset = queryset.filter(nombre__icontains=search)
        filtered = queryset.count()
        field = 'id' if _numero(request.POST.get('order[0][column]'), 1) == 0 else 'nombre'
        if request.POST.get('order[0][dir]') == 'desc':
            field = '-' + field
        queryset = queryset.order_by(field, 'pk')
        start = max(0, _numero(request.POST.get('start'), 0))
        length = _numero(request.POST.get('length'), 10)
        if length != -1:
            length = length if length > 0 else 10
            queryset = queryset[start:start + length]
        return JsonResponse({'draw': max(0, _numero(request.POST.get('draw'), 1)),
                             'recordsTotal': total, 'recordsFiltered': filtered,
                             'data': list(queryset.values('id', 'nombre'))})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            title='Listado de Funcionarios', resource_type='funcionario',
            create_url=reverse_lazy('inventario_tic:funcionario_create'),
            edit_url_template=reverse_lazy('inventario_tic:funcionario_update', kwargs={'pk': 0}),
            delete_url_template=reverse_lazy('inventario_tic:funcionario_deactivate', kwargs={'pk': 0}),
        )
        return context


class FuncionarioInventarioCreateView(StandardCreateView):
    model = FuncionarioInventario
    form_class = FormFuncionarioInventario
    template_name = 'inventario_tic/funcionarios_form.html'
    title = 'Crear Funcionario'
    success_url = reverse_lazy('inventario_tic:funcionario_list')

    def get_list_url(self):
        return self.success_url

    def form_valid(self, form):
        if not getattr(self.request.user, 'establecimiento_id', None):
            form.add_error(None, 'Debe tener un establecimiento asignado para crear funcionarios.')
            return self.form_invalid(form)
        return super().form_valid(form)


class FuncionarioInventarioUpdateView(StandardUpdateView):
    model = FuncionarioInventario
    form_class = FormFuncionarioInventario
    template_name = 'inventario_tic/funcionarios_form.html'
    title = 'Editar Funcionario'
    success_url = reverse_lazy('inventario_tic:funcionario_list')

    def get_list_url(self):
        return self.success_url

    def get_queryset(self):
        return funcionarios_visibles(self.request.user)


@login_required
@require_POST
def funcionario_desactivar(request, pk):
    funcionario = get_object_or_404(funcionarios_visibles(request.user), pk=pk)
    funcionario.is_active = False
    funcionario.updated_by = request.user
    funcionario.save(update_fields=['is_active', 'updated_by', 'updated_at'])
    return JsonResponse({'success': True, 'message': 'Funcionario desactivado correctamente.'})


@login_required
@require_POST
def funcionario_crear_modal(request):
    form = FormFuncionarioInventario(request.POST)
    if not getattr(request.user, 'establecimiento_id', None):
        form.is_valid()
        form.add_error(None, 'Debe tener un establecimiento asignado para crear funcionarios.')
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    if not form.is_valid():
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    funcionario = form.save(commit=False)
    funcionario.establecimiento = request.user.establecimiento
    funcionario.created_by = request.user
    funcionario.save()
    coincidencias = funcionarios_visibles(request.user).filter(nombre__iexact=funcionario.nombre).exclude(pk=funcionario.pk).exists()
    return JsonResponse({'success': True, 'id': funcionario.pk, 'nombre': funcionario.nombre,
                         'coincidencias': coincidencias}, status=201)
