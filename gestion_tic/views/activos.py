from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import OuterRef, Subquery, Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, CreateView, UpdateView

from gestion_tic.filters.activo import ActivoFormFilter
from gestion_tic.forms.activos import ActivoForm
from gestion_tic.models import Activo, TipoActivo, MovimientoActivo


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class ActivoListView(LoginRequiredMixin, TemplateView):
    template_name = 'gestion_tic/activos/activo_list.html'

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse({'error': 'Acción no válida'}, status=400)

        draw = int(request.POST.get('draw', 1))
        start = max(0, int(request.POST.get('start', 0)))
        length = int(request.POST.get('length', 10))

        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            queryset = Activo.objects.filter(
                establecimiento=request.user.establecimiento,
                is_active=True
            )
        else:
            queryset = Activo.objects.filter(is_active=True)

        records_total = queryset.count()

        # Filtros específicos
        tipo_id = request.POST.get('tipo') or request.GET.get('tipo')
        if tipo_id:
            queryset = queryset.filter(tipo_id=tipo_id)

        marca_id = request.POST.get('marca')
        if marca_id:
            queryset = queryset.filter(marca_id=marca_id)

        modelo_id = request.POST.get('modelo')
        if modelo_id:
            queryset = queryset.filter(modelo_id=modelo_id)

        contrato_id = request.POST.get('contrato')
        if contrato_id:
            queryset = queryset.filter(contrato_id=contrato_id)

        serie = request.POST.get('serie', '').strip()
        if serie:
            queryset = queryset.filter(serie__icontains=serie)

        codigo_barra = request.POST.get('codigo_barra', '').strip()
        if codigo_barra:
            queryset = queryset.filter(codigo_barra__icontains=codigo_barra)

        de_baja = request.POST.get('de_baja')
        if de_baja in ('true', '1', 'True'):
            queryset = queryset.filter(de_baja=True)
        elif de_baja in ('false', '0', 'False'):
            queryset = queryset.filter(de_baja=False)

        # Búsqueda global DataTables
        search = request.POST.get('search[value]', '').strip()
        if search:
            queryset = queryset.filter(
                Q(codigo_barra__icontains=search) |
                Q(serie__icontains=search) |
                Q(tipo__nombre__icontains=search) |
                Q(marca__nombre__icontains=search) |
                Q(modelo__nombre__icontains=search) |
                Q(contrato__nombre__icontains=search) |
                Q(observacion__icontains=search)
            )

        columnas = {
            0: 'id',
            1: 'codigo_barra',
            2: 'tipo__nombre',
            3: 'marca__nombre',
            4: 'modelo__nombre',
            5: 'serie',
            6: 'contrato__nombre',
            7: 'de_baja',
        }

        order_index = _as_int(request.POST.get('order[0][column]'), 1)
        order_dir = request.POST.get('order[0][dir]', 'asc')
        campo = columnas.get(order_index, 'codigo_barra')
        if order_dir == 'desc':
            campo = f'-{campo}'

        queryset = queryset.select_related('tipo', 'marca', 'modelo', 'contrato').prefetch_related(
            'movimientos').order_by(campo, 'pk')
        records_filtered = queryset.count()

        if length != -1:
            queryset = queryset[start:start + length]

        data = []
        for obj in queryset:
            ultimo_mov = obj.movimientos.first()
            acta_url = reverse('gestion_tic:activo_acta_pdf', kwargs={'pk': ultimo_mov.pk}) if ultimo_mov else None
            data.append({
                'id': obj.id,
                'codigo_barra': obj.codigo_barra,
                'tipo': obj.tipo.nombre if obj.tipo else '-',
                'tipo_id': obj.tipo_id if obj.tipo_id else '',
                'marca': obj.marca.nombre if obj.marca else '-',
                'modelo': obj.modelo.nombre if obj.modelo else '-',
                'marca_modelo': f"{obj.marca.nombre if obj.marca else '-'} / {obj.modelo.nombre if obj.modelo else '-'}",
                'serie': obj.serie or '-',
                'contrato': obj.contrato.nombre if obj.contrato else '-',
                'observacion': obj.observacion or '',
                'de_baja': obj.de_baja,
                'acta_url': acta_url,
            })

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Activos'
        context['resource_type'] = 'activo'
        context['create_url'] = reverse_lazy('gestion_tic:activo_create')
        context['edit_url_template'] = reverse_lazy('gestion_tic:activo_update', kwargs={'pk': 0})
        context['delete_url_template'] = reverse_lazy('gestion_tic:activo_deactivate', kwargs={'pk': 0})

        tipo_id = self.request.GET.get('tipo')
        context['tipo_id'] = tipo_id or ''

        establecimiento = getattr(self.request.user, 'establecimiento', None)
        context['filter_form'] = ActivoFormFilter(self.request.GET or None, establecimiento=establecimiento)
        if establecimiento:
            context['tipos_activos'] = TipoActivo.objects.filter(establecimiento=establecimiento, is_active=True)
        else:
            context['tipos_activos'] = TipoActivo.objects.filter(is_active=True)
        return context


class ActivoCreateView(LoginRequiredMixin, CreateView):
    model = Activo
    form_class = ActivoForm
    template_name = 'gestion_tic/activos/activo_form.html'
    title = 'Crear Activo'
    success_url = reverse_lazy('gestion_tic:activo_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        tipo_id = self.request.GET.get('tipo') or self.request.POST.get('tipo')
        if tipo_id:
            try:
                kwargs['tipo_activo'] = TipoActivo.objects.get(id=tipo_id)
            except (TipoActivo.DoesNotExist, ValueError):
                pass
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            kwargs['establecimiento'] = self.request.user.establecimiento
        return kwargs

    def form_valid(self, form):
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            form.instance.establecimiento = self.request.user.establecimiento
        if hasattr(form.instance, 'created_by'):
            form.instance.created_by = self.request.user
        form.instance.is_active = True
        self.object = form.save(commit=False)
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            self.object.establecimiento = self.request.user.establecimiento
        self.object.save()
        form.save_dynamic_fields(self.object)
        messages.success(self.request, 'Activo creado correctamente.')
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo_id = self.request.GET.get('tipo')
        tipo_activo = None
        if tipo_id:
            try:
                tipo_activo = TipoActivo.objects.get(id=tipo_id)
            except (TipoActivo.DoesNotExist, ValueError):
                pass
        context['tipo_activo'] = tipo_activo
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            context['tipos_activos'] = TipoActivo.objects.filter(establecimiento=self.request.user.establecimiento,
                                                                 is_active=True)
        else:
            context['tipos_activos'] = TipoActivo.objects.filter(is_active=True)
        context['title'] = self.title
        context['submit_label'] = 'Guardar Activo'
        context['list_url'] = reverse_lazy('gestion_tic:activo_list')
        return context


class ActivoUpdateView(LoginRequiredMixin, UpdateView):
    model = Activo
    form_class = ActivoForm
    template_name = 'gestion_tic/activos/activo_form.html'
    title = 'Editar Activo'
    success_url = reverse_lazy('gestion_tic:activo_list')

    def get_queryset(self):
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            return Activo.objects.filter(
                establecimiento=self.request.user.establecimiento,
                is_active=True
            )
        return Activo.objects.filter(is_active=True)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tipo_activo'] = self.object.tipo
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            kwargs['establecimiento'] = self.request.user.establecimiento
        return kwargs

    def form_valid(self, form):
        if hasattr(form.instance, 'updated_by'):
            form.instance.updated_by = self.request.user
        self.object = form.save(commit=False)
        self.object.save()
        form.save_dynamic_fields(self.object)
        messages.success(self.request, 'Activo actualizado correctamente.')
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activo'] = self.object
        context['tipo_activo'] = self.object.tipo
        context['title'] = f'Editar Activo: {self.object.codigo_barra}'
        context['submit_label'] = 'Actualizar Activo'
        context['list_url'] = reverse_lazy('gestion_tic:activo_list')
        return context


@login_required
@require_POST
def activo_desactivar(request, pk):
    if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
        obj = get_object_or_404(Activo, pk=pk, establecimiento=request.user.establecimiento)
    else:
        obj = get_object_or_404(Activo, pk=pk)
    obj.is_active = False
    if hasattr(obj, 'updated_by'):
        obj.updated_by = request.user
    obj.save()
    return JsonResponse({
        'success': True,
        'message': f'El activo "{obj.codigo_barra}" ha sido desactivado exitosamente.'
    })


# Compatibilidad retroactiva
activo_list = ActivoListView.as_view()
activo_create = ActivoCreateView.as_view()
activo_edit = ActivoUpdateView.as_view()


@login_required
def activo_list_asignado(request):
    establecimiento = getattr(request.user, 'establecimiento', None)
    ultimo_movimiento = MovimientoActivo.objects.filter(
        activo=OuterRef('activo')
    ).order_by('-updated_at', '-id')

    queryset = (
        MovimientoActivo.objects
        .filter(
            id=Subquery(ultimo_movimiento.values('id')[:1]),
            funcionario__isnull=False,
            activo__is_active=True,
            activo__de_baja=False
        )
    )
    if establecimiento:
        queryset = queryset.filter(establecimiento=establecimiento)

    action = request.POST.get('action') or request.GET.get('action')
    if action == 'search':
        draw = _as_int(request.POST.get('draw') or request.GET.get('draw'), 1)
        start = max(0, _as_int(request.POST.get('start') or request.GET.get('start'), 0))
        length = _as_int(request.POST.get('length') or request.GET.get('length'), 10)

        records_total = queryset.count()

        req_params = request.POST if request.method == 'POST' else request.GET

        tipo_id = req_params.get('tipo')
        if tipo_id:
            queryset = queryset.filter(activo__tipo_id=tipo_id)

        marca_id = req_params.get('marca')
        if marca_id:
            queryset = queryset.filter(activo__marca_id=marca_id)

        modelo_id = req_params.get('modelo')
        if modelo_id:
            queryset = queryset.filter(activo__modelo_id=modelo_id)

        contrato_id = req_params.get('contrato')
        if contrato_id:
            queryset = queryset.filter(activo__contrato_id=contrato_id)

        serie = req_params.get('serie', '').strip()
        if serie:
            queryset = queryset.filter(activo__serie__icontains=serie)

        codigo_barra = req_params.get('codigo_barra', '').strip()
        if codigo_barra:
            queryset = queryset.filter(activo__codigo_barra__icontains=codigo_barra)

        search = req_params.get('search[value]', '').strip()
        if search:
            queryset = queryset.filter(
                Q(activo__codigo_barra__icontains=search) |
                Q(activo__serie__icontains=search) |
                Q(activo__tipo__nombre__icontains=search) |
                Q(activo__marca__nombre__icontains=search) |
                Q(activo__modelo__nombre__icontains=search) |
                Q(activo__contrato__nombre__icontains=search) |
                Q(funcionario__nombres__icontains=search) |
                Q(funcionario__apellidos__icontains=search) |
                Q(funcionario__unidad_organizacional__nombre__icontains=search) |
                Q(ip__ip__icontains=search)
            )

        columnas = {
            0: 'id',
            1: 'activo__codigo_barra',
            2: 'activo__tipo__nombre',
            3: 'activo__marca__nombre',
            4: 'activo__serie',
            5: 'ip__ip',
            6: 'funcionario__nombres',
            7: 'funcionario__unidad_organizacional__nombre',
        }

        order_index = _as_int(req_params.get('order[0][column]'), 1)
        order_dir = req_params.get('order[0][dir]', 'asc')
        campo = columnas.get(order_index, 'activo__codigo_barra')
        if order_dir == 'desc':
            campo = f'-{campo}'

        queryset = queryset.select_related(
            'activo', 'activo__tipo', 'activo__marca', 'activo__modelo', 'activo__contrato',
            'funcionario', 'funcionario__unidad_organizacional', 'funcionario__unidad_organizacional__padre',
            'ip'
        ).order_by(campo, 'pk')

        records_filtered = queryset.count()

        if length != -1:
            queryset = queryset[start:start + length]

        data = []
        for mov in queryset:
            func_nombre = '-'
            if mov.funcionario:
                if hasattr(mov.funcionario, 'nombre') and mov.funcionario.nombre:
                    func_nombre = mov.funcionario.nombre
                else:
                    parts = [mov.funcionario.nombres or '', mov.funcionario.apellidos or '']
                    func_nombre = ' '.join(p for p in parts if p).strip() or '-'

            unidad_nombre = '-'
            unidad_padre = ''
            if mov.funcionario and mov.funcionario.unidad_organizacional:
                unidad_nombre = mov.funcionario.unidad_organizacional.nombre or '-'
                if mov.funcionario.unidad_organizacional.padre:
                    unidad_padre = mov.funcionario.unidad_organizacional.padre.nombre or ''

            data.append({
                'id': mov.id,
                'activo_id': mov.activo.id if mov.activo else '',
                'codigo_barra': mov.activo.codigo_barra if mov.activo else '-',
                'tipo': mov.activo.tipo.nombre if (mov.activo and mov.activo.tipo) else '-',
                'marca_modelo': f"{mov.activo.marca.nombre if (mov.activo and mov.activo.marca) else '-'} / {mov.activo.modelo.nombre if (mov.activo and mov.activo.modelo) else '-'}",
                'serie': mov.activo.serie if (mov.activo and mov.activo.serie) else '-',
                'ip': mov.ip.ip if mov.ip else '-',
                'funcionario': func_nombre,
                'unidad_organizacional': unidad_nombre,
                'unidad_padre': unidad_padre,
                'acta_url': reverse('gestion_tic:activo_acta_pdf', kwargs={'pk': mov.id}),
                'edit_url': reverse('gestion_tic:activo_update', kwargs={'pk': mov.activo.id}) if mov.activo else '#',
            })

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })

    filter_form = ActivoFormFilter(request.GET or None, establecimiento=establecimiento)
    return render(request, 'gestion_tic/activos/activos_asignados.html', {
        'title': 'Listado de Activos Asignados',
        'filter_form': filter_form,
        'edit_url_template': reverse_lazy('gestion_tic:activo_update', kwargs={'pk': 0}),
        'url_form': reverse_lazy('gestion_tic:activo_create'),
    })
