from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, CreateView, UpdateView

from ..forms.mantenedores import (
    FormMarca, FormContrato, FormIps, FormJefeTic, FormModelo, FormPropietario, FormEstablecimiento, FormTipoProducto
)
from ..models.mantenedores import (
    Marca, Contrato, Ips, JefeTic,
    Modelo, Propietario, Establecimiento, TipoProducto,
)


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ==============================================================================
# 1. MARCA
# ==============================================================================

class MarcaListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventario_tic/mantenedores_list.html'

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse({'error': 'Acción no válida'}, status=400)

        draw = int(request.POST.get('draw', 1))
        start = max(0, int(request.POST.get('start', 0)))
        length = int(request.POST.get('length', 10))

        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            queryset = Marca.objects.filter(
                establecimiento=request.user.establecimiento,
                is_active=True
            )
        else:
            queryset = Marca.objects.filter(is_active=True)

        records_total = queryset.count()

        search = request.POST.get('search[value]', '').strip()
        if search:
            queryset = queryset.filter(Q(nombre__icontains=search))

        columnas = {
            0: 'id',
            1: 'nombre',
        }

        order_index = _as_int(request.POST.get('order[0][column]'), 1)
        order_dir = request.POST.get('order[0][dir]', 'asc')
        campo = columnas.get(order_index, 'nombre')
        if order_dir == 'desc':
            campo = f'-{campo}'

        queryset = queryset.order_by(campo, 'pk')
        records_filtered = queryset.count()

        if length != -1:
            queryset = queryset[start:start + length]

        data = list(queryset.values('id', 'nombre'))

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Marcas'
        context['resource_type'] = 'marca'
        context['create_url'] = reverse_lazy('inventario_tic:marca_create')
        context['edit_url_template'] = reverse_lazy('inventario_tic:marca_update', kwargs={'pk': 0})
        context['delete_url_template'] = reverse_lazy('inventario_tic:marca_deactivate', kwargs={'pk': 0})
        return context


class MarcaCreateView(LoginRequiredMixin, CreateView):
    model = Marca
    form_class = FormMarca
    template_name = 'inventario_tic/mantenedores_form.html'
    title = 'Crear Marca'
    success_url = reverse_lazy('inventario_tic:marca_list')

    def form_valid(self, form):
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            form.instance.establecimiento = self.request.user.establecimiento
        if hasattr(form.instance, 'created_by'):
            form.instance.created_by = self.request.user
        messages.success(self.request, 'Marca creada correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['submit_label'] = 'Guardar'
        context['list_url'] = reverse_lazy('inventario_tic:marca_list')
        return context


class MarcaUpdateView(LoginRequiredMixin, UpdateView):
    model = Marca
    form_class = FormMarca
    template_name = 'inventario_tic/mantenedores_form.html'
    title = 'Editar Marca'
    success_url = reverse_lazy('inventario_tic:marca_list')

    def get_queryset(self):
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            return Marca.objects.filter(
                establecimiento=self.request.user.establecimiento,
                is_active=True
            )
        return Marca.objects.filter(is_active=True)

    def form_valid(self, form):
        if hasattr(form.instance, 'updated_by'):
            form.instance.updated_by = self.request.user
        messages.success(self.request, 'Marca actualizada correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['submit_label'] = 'Actualizar'
        context['list_url'] = reverse_lazy('inventario_tic:marca_list')
        return context


@login_required
@require_POST
def marca_desactivar(request, pk):
    try:
        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            obj = get_object_or_404(Marca, pk=pk, establecimiento=request.user.establecimiento)
        else:
            obj = get_object_or_404(Marca, pk=pk)

        nombre = str(obj.nombre)
        obj.is_active = False
        if hasattr(obj, 'updated_by'):
            obj.updated_by = request.user
        obj.save()

        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': f'La marca "{nombre}" (ID: {pk}) fue desactivada correctamente.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': f'Ocurrió un error al intentar desactivar el registro: {str(e)}'
        }, status=400)


# ==============================================================================
# 2. MODELO
# ==============================================================================

class ModeloListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventario_tic/mantenedores_list.html'

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse({'error': 'Acción no válida'}, status=400)

        draw = int(request.POST.get('draw', 1))
        start = max(0, int(request.POST.get('start', 0)))
        length = int(request.POST.get('length', 10))

        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            queryset = Modelo.objects.filter(
                establecimiento=request.user.establecimiento,
                is_active=True
            )
        else:
            queryset = Modelo.objects.filter(is_active=True)

        records_total = queryset.count()

        search = request.POST.get('search[value]', '').strip()
        if search:
            queryset = queryset.filter(Q(nombre__icontains=search))
            queryset = queryset.filter(Q(marca__nombre__icontains=search))

        columnas = {
            0: 'id',
            1: 'nombre',
            2: 'marca'
        }

        order_index = _as_int(request.POST.get('order[0][column]'), 1)
        order_dir = request.POST.get('order[0][dir]', 'asc')
        campo = columnas.get(order_index, 'nombre')
        if order_dir == 'desc':
            campo = f'-{campo}'

        queryset = queryset.order_by(campo, 'pk')
        records_filtered = queryset.count()

        if length != -1:
            queryset = queryset[start:start + length]

        data = list(queryset.values('id', 'nombre', 'marca'))

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Modelos'
        context['resource_type'] = 'modelo'
        context['create_url'] = reverse_lazy('inventario_tic:modelo_create')
        context['edit_url_template'] = reverse_lazy('inventario_tic:modelo_update', kwargs={'pk': 0})
        context['delete_url_template'] = reverse_lazy('inventario_tic:modelo_deactivate', kwargs={'pk': 0})
        return context


class ModeloCreateView(LoginRequiredMixin, CreateView):
    model = Modelo
    form_class = FormModelo
    template_name = 'inventario_tic/mantenedores_form.html'
    title = 'Crear Modelo'
    success_url = reverse_lazy('inventario_tic:modelo_list')

    def form_valid(self, form):
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            form.instance.establecimiento = self.request.user.establecimiento
        if hasattr(form.instance, 'created_by'):
            form.instance.created_by = self.request.user
        messages.success(self.request, 'Modelo creado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['submit_label'] = 'Guardar'
        context['list_url'] = reverse_lazy('inventario_tic:modelo_list')
        return context


class ModeloUpdateView(LoginRequiredMixin, UpdateView):
    model = Modelo
    form_class = FormModelo
    template_name = 'inventario_tic/mantenedores_form.html'
    title = 'Editar Modelo'
    success_url = reverse_lazy('inventario_tic:modelo_list')

    def get_queryset(self):
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            return Modelo.objects.filter(
                establecimiento=self.request.user.establecimiento,
                is_active=True
            )
        return Modelo.objects.filter(is_active=True)

    def form_valid(self, form):
        if hasattr(form.instance, 'updated_by'):
            form.instance.updated_by = self.request.user
        messages.success(self.request, 'Modelo actualizado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['submit_label'] = 'Actualizar'
        context['list_url'] = reverse_lazy('inventario_tic:modelo_list')
        return context


@login_required
@require_POST
def modelo_desactivar(request, pk):
    try:
        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            obj = get_object_or_404(Modelo, pk=pk, establecimiento=request.user.establecimiento)
        else:
            obj = get_object_or_404(Modelo, pk=pk)

        nombre = str(obj.nombre)
        obj.is_active = False
        if hasattr(obj, 'updated_by'):
            obj.updated_by = request.user
        obj.save()

        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': f'El modelo "{nombre}" (ID: {pk}) fue desactivado correctamente.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': f'Ocurrió un error al intentar desactivar el registro: {str(e)}'
        }, status=400)


# ==============================================================================
# 3. PROPIETARIO
# ==============================================================================

class PropietarioListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventario_tic/mantenedores_list.html'

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse({'error': 'Acción no válida'}, status=400)

        draw = int(request.POST.get('draw', 1))
        start = max(0, int(request.POST.get('start', 0)))
        length = int(request.POST.get('length', 10))

        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            queryset = Propietario.objects.filter(
                establecimiento=request.user.establecimiento,
                is_active=True
            )
        else:
            queryset = Propietario.objects.filter(is_active=True)

        records_total = queryset.count()

        search = request.POST.get('search[value]', '').strip()
        if search:
            queryset = queryset.filter(Q(nombre__icontains=search))

        columnas = {
            0: 'id',
            1: 'nombre',
        }

        order_index = _as_int(request.POST.get('order[0][column]'), 1)
        order_dir = request.POST.get('order[0][dir]', 'asc')
        campo = columnas.get(order_index, 'nombre')
        if order_dir == 'desc':
            campo = f'-{campo}'

        queryset = queryset.order_by(campo, 'pk')
        records_filtered = queryset.count()

        if length != -1:
            queryset = queryset[start:start + length]

        data = list(queryset.values('id', 'nombre'))

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Propietarios'
        context['resource_type'] = 'propietario'
        context['create_url'] = reverse_lazy('inventario_tic:propietario_create')
        context['edit_url_template'] = reverse_lazy('inventario_tic:propietario_update', kwargs={'pk': 0})
        context['delete_url_template'] = reverse_lazy('inventario_tic:propietario_deactivate', kwargs={'pk': 0})
        return context


class PropietarioCreateView(LoginRequiredMixin, CreateView):
    model = Propietario
    form_class = FormPropietario
    template_name = 'inventario_tic/mantenedores_form.html'
    title = 'Crear Propietario'
    success_url = reverse_lazy('inventario_tic:propietario_list')

    def form_valid(self, form):
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            form.instance.establecimiento = self.request.user.establecimiento
        if hasattr(form.instance, 'created_by'):
            form.instance.created_by = self.request.user
        messages.success(self.request, 'Propietario creado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['submit_label'] = 'Guardar'
        context['list_url'] = reverse_lazy('inventario_tic:propietario_list')
        return context


class PropietarioUpdateView(LoginRequiredMixin, UpdateView):
    model = Propietario
    form_class = FormPropietario
    template_name = 'inventario_tic/mantenedores_form.html'
    title = 'Editar Propietario'
    success_url = reverse_lazy('inventario_tic:propietario_list')

    def get_queryset(self):
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            return Propietario.objects.filter(
                establecimiento=self.request.user.establecimiento,
                is_active=True
            )
        return Propietario.objects.filter(is_active=True)

    def form_valid(self, form):
        if hasattr(form.instance, 'updated_by'):
            form.instance.updated_by = self.request.user
        messages.success(self.request, 'Propietario actualizado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['submit_label'] = 'Actualizar'
        context['list_url'] = reverse_lazy('inventario_tic:propietario_list')
        return context


@login_required
@require_POST
def propietario_desactivar(request, pk):
    try:
        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            obj = get_object_or_404(Propietario, pk=pk, establecimiento=request.user.establecimiento)
        else:
            obj = get_object_or_404(Propietario, pk=pk)

        nombre = str(obj.nombre)
        obj.is_active = False
        if hasattr(obj, 'updated_by'):
            obj.updated_by = request.user
        obj.save()

        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': f'El propietario "{nombre}" (ID: {pk}) fue desactivado correctamente.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': f'Ocurrió un error al intentar desactivar el registro: {str(e)}'
        }, status=400)


# ==============================================================================
# 4. JEFE TIC
# ==============================================================================

class JefeTicListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventario_tic/mantenedores_list.html'

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse({'error': 'Acción no válida'}, status=400)

        draw = int(request.POST.get('draw', 1))
        start = max(0, int(request.POST.get('start', 0)))
        length = int(request.POST.get('length', 10))

        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            queryset = JefeTic.objects.filter(
                establecimiento=request.user.establecimiento,
                is_active=True
            )
        else:
            queryset = JefeTic.objects.filter(is_active=True)

        records_total = queryset.count()

        search = request.POST.get('search[value]', '').strip()
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(posicion__icontains=search)
            )

        columnas = {
            0: 'id',
            1: 'nombre',
            2: 'posicion',
        }

        order_index = _as_int(request.POST.get('order[0][column]'), 1)
        order_dir = request.POST.get('order[0][dir]', 'asc')
        campo = columnas.get(order_index, 'nombre')
        if order_dir == 'desc':
            campo = f'-{campo}'

        queryset = queryset.order_by(campo, 'pk')
        records_filtered = queryset.count()

        if length != -1:
            queryset = queryset[start:start + length]

        data = list(queryset.values('id', 'nombre', 'posicion'))

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Jefes TIC'
        context['resource_type'] = 'jefetic'
        context['has_posicion'] = True
        context['create_url'] = reverse_lazy('inventario_tic:jefetic_create')
        context['edit_url_template'] = reverse_lazy('inventario_tic:jefetic_update', kwargs={'pk': 0})
        context['delete_url_template'] = reverse_lazy('inventario_tic:jefetic_deactivate', kwargs={'pk': 0})
        return context


class JefeTicCreateView(LoginRequiredMixin, CreateView):
    model = JefeTic
    form_class = FormJefeTic
    template_name = 'inventario_tic/mantenedores_form.html'
    title = 'Crear Jefe TIC'
    success_url = reverse_lazy('inventario_tic:jefetic_list')

    def form_valid(self, form):
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            form.instance.establecimiento = self.request.user.establecimiento
        if hasattr(form.instance, 'created_by'):
            form.instance.created_by = self.request.user
        messages.success(self.request, 'Jefe TIC creado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['submit_label'] = 'Guardar'
        context['list_url'] = reverse_lazy('inventario_tic:jefetic_list')
        return context


class JefeTicUpdateView(LoginRequiredMixin, UpdateView):
    model = JefeTic
    form_class = FormJefeTic
    template_name = 'inventario_tic/mantenedores_form.html'
    title = 'Editar Jefe TIC'
    success_url = reverse_lazy('inventario_tic:jefetic_list')

    def get_queryset(self):
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            return JefeTic.objects.filter(
                establecimiento=self.request.user.establecimiento,
                is_active=True
            )
        return JefeTic.objects.filter(is_active=True)

    def form_valid(self, form):
        if hasattr(form.instance, 'updated_by'):
            form.instance.updated_by = self.request.user
        messages.success(self.request, 'Jefe TIC actualizado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['submit_label'] = 'Actualizar'
        context['list_url'] = reverse_lazy('inventario_tic:jefetic_list')
        return context


@login_required
@require_POST
def jefetic_desactivar(request, pk):
    try:
        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            obj = get_object_or_404(JefeTic, pk=pk, establecimiento=request.user.establecimiento)
        else:
            obj = get_object_or_404(JefeTic, pk=pk)

        nombre = str(obj.nombre)
        obj.is_active = False
        if hasattr(obj, 'updated_by'):
            obj.updated_by = request.user
        obj.save()

        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': f'El Jefe TIC "{nombre}" (ID: {pk}) fue desactivado correctamente.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': f'Ocurrió un error al intentar desactivar el registro: {str(e)}'
        }, status=400)


# ==============================================================================
# 5. CONTRATO
# ==============================================================================

class ContratoListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventario_tic/mantenedores_list.html'

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse({'error': 'Acción no válida'}, status=400)

        draw = int(request.POST.get('draw', 1))
        start = max(0, int(request.POST.get('start', 0)))
        length = int(request.POST.get('length', 10))

        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            queryset = Contrato.objects.filter(
                establecimiento=request.user.establecimiento,
                is_active=True
            )
        else:
            queryset = Contrato.objects.filter(is_active=True)

        records_total = queryset.count()

        search = request.POST.get('search[value]', '').strip()
        if search:
            queryset = queryset.filter(Q(nombre__icontains=search))

        columnas = {
            0: 'id',
            1: 'nombre',
        }

        order_index = _as_int(request.POST.get('order[0][column]'), 1)
        order_dir = request.POST.get('order[0][dir]', 'asc')
        campo = columnas.get(order_index, 'nombre')
        if order_dir == 'desc':
            campo = f'-{campo}'

        queryset = queryset.order_by(campo, 'pk')
        records_filtered = queryset.count()

        if length != -1:
            queryset = queryset[start:start + length]

        data = []
        for c in queryset:
            data.append({
                'id': c.id,
                'nombre': c.nombre,
                'file_url': c.file.url if c.file else None,
            })

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Contratos'
        context['resource_type'] = 'contrato'
        context['has_file'] = True
        context['create_url'] = reverse_lazy('inventario_tic:contrato_create')
        context['edit_url_template'] = reverse_lazy('inventario_tic:contrato_update', kwargs={'pk': 0})
        context['delete_url_template'] = reverse_lazy('inventario_tic:contrato_deactivate', kwargs={'pk': 0})
        return context


class ContratoCreateView(LoginRequiredMixin, CreateView):
    model = Contrato
    form_class = FormContrato
    template_name = 'inventario_tic/mantenedores_form.html'
    title = 'Crear Contrato'
    success_url = reverse_lazy('inventario_tic:contrato_list')

    def form_valid(self, form):
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            form.instance.establecimiento = self.request.user.establecimiento
        if hasattr(form.instance, 'created_by'):
            form.instance.created_by = self.request.user
        messages.success(self.request, 'Contrato creado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['submit_label'] = 'Guardar'
        context['list_url'] = reverse_lazy('inventario_tic:contrato_list')
        return context


class ContratoUpdateView(LoginRequiredMixin, UpdateView):
    model = Contrato
    form_class = FormContrato
    template_name = 'inventario_tic/mantenedores_form.html'
    title = 'Editar Contrato'
    success_url = reverse_lazy('inventario_tic:contrato_list')

    def get_queryset(self):
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            return Contrato.objects.filter(
                establecimiento=self.request.user.establecimiento,
                is_active=True
            )
        return Contrato.objects.filter(is_active=True)

    def form_valid(self, form):
        if hasattr(form.instance, 'updated_by'):
            form.instance.updated_by = self.request.user
        messages.success(self.request, 'Contrato actualizado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['submit_label'] = 'Actualizar'
        context['list_url'] = reverse_lazy('inventario_tic:contrato_list')
        return context


@login_required
@require_POST
def contrato_desactivar(request, pk):
    try:
        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            obj = get_object_or_404(Contrato, pk=pk, establecimiento=request.user.establecimiento)
        else:
            obj = get_object_or_404(Contrato, pk=pk)

        nombre = str(obj.nombre)
        obj.is_active = False
        if hasattr(obj, 'updated_by'):
            obj.updated_by = request.user
        obj.save()

        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': f'El contrato "{nombre}" (ID: {pk}) fue desactivado correctamente.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': f'Ocurrió un error al intentar desactivar el registro: {str(e)}'
        }, status=400)


# ==============================================================================
# 6. IPS
# ==============================================================================

class IpsListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventario_tic/ips_list.html'

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse({'error': 'Acción no válida'}, status=400)

        draw = int(request.POST.get('draw', 1))
        start = max(0, int(request.POST.get('start', 0)))
        length = int(request.POST.get('length', 10))

        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            queryset = Ips.objects.filter(
                establecimiento=request.user.establecimiento,
                is_active=True
            )
        else:
            queryset = Ips.objects.filter(is_active=True)

        segmento = request.POST.get('segmento', '').strip() or request.GET.get('segmento', '').strip()
        if segmento:
            prefix = segmento.replace('.x', '.')
            if not prefix.endswith('.'):
                prefix += '.'
            queryset = queryset.filter(ip__startswith=prefix)

        records_total = queryset.count()

        search = request.POST.get('search[value]', '').strip()
        if search:
            queryset = queryset.filter(
                Q(ip__icontains=search) |
                Q(mascara__icontains=search) |
                Q(gateway__icontains=search) |
                Q(vlan__icontains=search) |
                Q(observacion__icontains=search)
            )

        columnas = {
            0: 'id',
            1: 'ip',
            2: 'mascara',
            3: 'gateway',
            4: 'vlan',
            5: 'asignado',
            6: 'observacion',
        }

        order_index = _as_int(request.POST.get('order[0][column]'), 1)
        order_dir = request.POST.get('order[0][dir]', 'asc')
        campo = columnas.get(order_index, 'ip')
        if order_dir == 'desc':
            campo = f'-{campo}'

        queryset = queryset.order_by(campo, 'pk')
        records_filtered = queryset.count()

        if length != -1:
            queryset = queryset[start:start + length]

        data = list(queryset.values(
            'id', 'ip', 'mascara', 'gateway', 'vlan', 'asignado', 'observacion'
        ))

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Direcciones IP'
        context['resource_type'] = 'ips'
        context['create_url'] = reverse_lazy('inventario_tic:ips_create')
        context['edit_url_template'] = reverse_lazy('inventario_tic:ips_update', kwargs={'pk': 0})
        context['delete_url_template'] = reverse_lazy('inventario_tic:ips_deactivate', kwargs={'pk': 0})

        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            all_ips = Ips.objects.filter(
                establecimiento=self.request.user.establecimiento,
                is_active=True
            ).values_list('ip', flat=True)
        else:
            all_ips = Ips.objects.filter(is_active=True).values_list('ip', flat=True)

        segmentos_set = set()
        for ip in all_ips:
            parts = ip.strip().split('.')
            if len(parts) == 4:
                segmentos_set.add(f"{parts[0]}.{parts[1]}.{parts[2]}.x")

        def sort_key(seg):
            parts = seg.replace('.x', '').split('.')
            try:
                return [int(p) for p in parts]
            except ValueError:
                return [0, 0, 0]

        context['segmentos_ip'] = sorted(list(segmentos_set), key=sort_key)
        return context


class IpsCreateView(LoginRequiredMixin, CreateView):
    model = Ips
    form_class = FormIps
    template_name = 'inventario_tic/ips_form.html'
    title = 'Crear Dirección IP'
    success_url = reverse_lazy('inventario_tic:ips_list')

    def form_valid(self, form):
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            form.instance.establecimiento = self.request.user.establecimiento
        if hasattr(form.instance, 'created_by'):
            form.instance.created_by = self.request.user
        messages.success(self.request, 'Dirección IP creada correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['submit_label'] = 'Guardar'
        context['list_url'] = reverse_lazy('inventario_tic:ips_list')
        return context


class IpsUpdateView(LoginRequiredMixin, UpdateView):
    model = Ips
    form_class = FormIps
    template_name = 'inventario_tic/ips_form.html'
    title = 'Editar Dirección IP'
    success_url = reverse_lazy('inventario_tic:ips_list')

    def get_queryset(self):
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            return Ips.objects.filter(
                establecimiento=self.request.user.establecimiento,
                is_active=True
            )
        return Ips.objects.filter(is_active=True)

    def form_valid(self, form):
        if hasattr(form.instance, 'updated_by'):
            form.instance.updated_by = self.request.user
        messages.success(self.request, 'Dirección IP actualizada correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['submit_label'] = 'Actualizar'
        context['list_url'] = reverse_lazy('inventario_tic:ips_list')
        return context


@login_required
@require_POST
def ips_desactivar(request, pk):
    try:
        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            obj = get_object_or_404(Ips, pk=pk, establecimiento=request.user.establecimiento)
        else:
            obj = get_object_or_404(Ips, pk=pk)

        nombre = str(obj.ip)
        obj.is_active = False
        if hasattr(obj, 'updated_by'):
            obj.updated_by = request.user
        obj.save()

        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': f'La dirección IP "{nombre}" (ID: {pk}) fue desactivada correctamente.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': f'Ocurrió un error al intentar desactivar el registro: {str(e)}'
        }, status=400)


class EstablecimientoListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventario_tic/mantenedores_list.html'

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse({'error': 'Acción no válida'}, status=400)

        draw = int(request.POST.get('draw', 1))
        start = max(0, int(request.POST.get('start', 0)))
        length = int(request.POST.get('length', 10))

        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            queryset = Establecimiento.objects.filter(
                establecimiento=request.user.establecimiento,
                is_active=True
            )
        else:
            queryset = Establecimiento.objects.filter(is_active=True)

        records_total = queryset.count()

        search = request.POST.get('search[value]', '').strip()
        if search:
            queryset = queryset.filter(Q(nombre__icontains=search))

        columnas = {
            0: 'id',
            1: 'nombre',
        }

        order_index = _as_int(request.POST.get('order[0][column]'), 1)
        order_dir = request.POST.get('order[0][dir]', 'asc')
        campo = columnas.get(order_index, 'nombre')
        if order_dir == 'desc':
            campo = f'-{campo}'

        queryset = queryset.order_by(campo, 'pk')
        records_filtered = queryset.count()

        if length != -1:
            queryset = queryset[start:start + length]

        data = list(queryset.values('id', 'nombre'))

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Establecimientos'
        context['resource_type'] = 'establecimiento'
        context['create_url'] = reverse_lazy('inventario_tic:establecimiento_create')
        context['edit_url_template'] = reverse_lazy('inventario_tic:establecimiento_update', kwargs={'pk': 0})
        context['delete_url_template'] = reverse_lazy('inventario_tic:establecimiento_deactivate', kwargs={'pk': 0})
        return context


class EstablecimientoCreateView(LoginRequiredMixin, CreateView):
    model = Establecimiento
    form_class = FormEstablecimiento
    template_name = 'inventario_tic/mantenedores_form.html'
    title = 'Crear Establecimiento'
    success_url = reverse_lazy('inventario_tic:establecimiento_list')

    def form_valid(self, form):
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            form.instance.establecimiento = self.request.user.establecimiento
        if hasattr(form.instance, 'created_by'):
            form.instance.created_by = self.request.user
        messages.success(self.request, 'Establecimiento creado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['submit_label'] = 'Guardar'
        context['list_url'] = reverse_lazy('inventario_tic:establecimiento_list')
        return context


class EstablecimientoUpdateView(LoginRequiredMixin, UpdateView):
    model = Establecimiento
    form_class = FormEstablecimiento
    template_name = 'inventario_tic/mantenedores_form.html'
    title = 'Editar Establecimiento'
    success_url = reverse_lazy('inventario_tic:establecimiento_list')

    def get_queryset(self):
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            return Establecimiento.objects.filter(
                establecimiento=self.request.user.establecimiento,
                is_active=True
            )
        return Establecimiento.objects.filter(is_active=True)

    def form_valid(self, form):
        if hasattr(form.instance, 'updated_by'):
            form.instance.updated_by = self.request.user
        messages.success(self.request, 'Establecimiento actualizado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['submit_label'] = 'Actualizar'
        context['list_url'] = reverse_lazy('inventario_tic:establecimiento_list')
        return context


@login_required
@require_POST
def establecimiento_desactivar(request, pk):
    try:
        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            obj = get_object_or_404(Establecimiento, pk=pk, establecimiento=request.user.establecimiento)
        else:
            obj = get_object_or_404(Establecimiento, pk=pk)

        nombre = str(obj.nombre)
        obj.is_active = False
        if hasattr(obj, 'updated_by'):
            obj.updated_by = request.user
        obj.save()

        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': f'El establecimiento "{nombre}" (ID: {pk}) fue desactivado correctamente.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': f'Ocurrió un error al intentar desactivar el registro: {str(e)}'
        }, status=400)

class TipoProductoListView(LoginRequiredMixin, TemplateView):
    template_name = 'inventario_tic/mantenedores_list.html'

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse({'error': 'Acción no válida'}, status=400)

        draw = int(request.POST.get('draw', 1))
        start = max(0, int(request.POST.get('start', 0)))
        length = int(request.POST.get('length', 10))

        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            queryset = TipoProducto.objects.filter(
                establecimiento=request.user.establecimiento,
                is_active=True
            )
        else:
            queryset = TipoProducto.objects.filter(is_active=True)

        records_total = queryset.count()

        search = request.POST.get('search[value]', '').strip()
        if search:
            queryset = queryset.filter(Q(nombre__icontains=search))

        columnas = {
            0: 'id',
            1: 'nombre',
        }

        order_index = _as_int(request.POST.get('order[0][column]'), 1)
        order_dir = request.POST.get('order[0][dir]', 'asc')
        campo = columnas.get(order_index, 'nombre')
        if order_dir == 'desc':
            campo = f'-{campo}'

        queryset = queryset.order_by(campo, 'pk')
        records_filtered = queryset.count()

        if length != -1:
            queryset = queryset[start:start + length]

        data = list(queryset.values('id', 'nombre'))

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Tipos de Producto'
        context['resource_type'] = 'tipo_producto'
        context['create_url'] = reverse_lazy('inventario_tic:tipo_producto_create')
        context['edit_url_template'] = reverse_lazy('inventario_tic:tipo_producto_update', kwargs={'pk': 0})
        context['delete_url_template'] = reverse_lazy('inventario_tic:tipo_producto_deactivate', kwargs={'pk': 0})
        return context


class TipoProductoCreateView(LoginRequiredMixin, CreateView):
    model = TipoProducto
    form_class = FormTipoProducto
    template_name = 'inventario_tic/mantenedores_form.html'
    title = 'Crear Tipo de Producto'
    success_url = reverse_lazy('inventario_tic:tipo_producto_list')

    def form_valid(self, form):
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            form.instance.establecimiento = self.request.user.establecimiento
        if hasattr(form.instance, 'created_by'):
            form.instance.created_by = self.request.user
        messages.success(self.request, 'Tipo de producto creado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['submit_label'] = 'Guardar'
        context['list_url'] = reverse_lazy('inventario_tic:tipo_producto_list')
        return context


class TipoProductoUpdateView(LoginRequiredMixin, UpdateView):
    model = TipoProducto
    form_class = FormTipoProducto
    template_name = 'inventario_tic/mantenedores_form.html'
    title = 'Editar Tipo de Producto'
    success_url = reverse_lazy('inventario_tic:tipo_producto_list')

    def get_queryset(self):
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            return TipoProducto.objects.filter(
                establecimiento=self.request.user.establecimiento,
                is_active=True
            )
        return TipoProducto.objects.filter(is_active=True)

    def form_valid(self, form):
        if hasattr(form.instance, 'updated_by'):
            form.instance.updated_by = self.request.user
        messages.success(self.request, 'Tipo de producto actualizado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['submit_label'] = 'Actualizar'
        context['list_url'] = reverse_lazy('inventario_tic:tipo_producto_list')
        return context


@login_required
@require_POST
def tipo_producto_desactivar(request, pk):
    try:
        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            obj = get_object_or_404(TipoProducto, pk=pk, establecimiento=request.user.establecimiento)
        else:
            obj = get_object_or_404(TipoProducto, pk=pk)

        nombre = str(obj.nombre)
        obj.is_active = False
        if hasattr(obj, 'updated_by'):
            obj.updated_by = request.user
        obj.save()

        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': f'El tipo de producto "{nombre}" (ID: {pk}) fue desactivado correctamente.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': f'Ocurrió un error al intentar desactivar el registro: {str(e)}'
        }, status=400)


