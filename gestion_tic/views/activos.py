from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import OuterRef, Subquery, Q, Exists, F, Value, Case, When, FloatField, IntegerField, DateField
from django.db.models.functions import Cast, NullIf
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, CreateView, UpdateView

from gestion_tic.filters.activo import ActivoFormFilter
from gestion_tic.forms.activos import ActivoForm
from gestion_tic.models import Activo, TipoActivo, MovimientoActivo, CampoTipoActivo, ActivoCaracteristica


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _format_caracteristica_value(valor, tipo_campo):
    if valor is None or str(valor).strip() == '':
        return '-'
    val_str = str(valor).strip()
    if tipo_campo == 'boolean':
        if val_str.lower() in ('true', '1', 'si', 'sí', 'si', 'true'):
            return 'Sí'
        elif val_str.lower() in ('false', '0', 'no', 'false'):
            return 'No'
        return val_str
    elif tipo_campo == 'date':
        try:
            dt = datetime.strptime(val_str, '%Y-%m-%d')
            return dt.strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            return val_str
    return val_str


def _get_tipo_activo_or_404(tipo_id, user_establecimiento=None):
    if tipo_id is None or str(tipo_id).strip() == '':
        return None
    try:
        pk = int(tipo_id)
    except (TypeError, ValueError):
        raise Http404("El tipo de activo no existe.")

    tipo_qs = TipoActivo.objects.filter(id=pk, is_active=True)
    if user_establecimiento:
        tipo_qs = tipo_qs.filter(establecimiento=user_establecimiento)
    tipo_activo = tipo_qs.first()
    if not tipo_activo:
        raise Http404("El tipo de activo no existe.")
    return tipo_activo


def _get_campos_for_tipo(tipo_id, user_establecimiento=None):
    tipo_activo = _get_tipo_activo_or_404(tipo_id, user_establecimiento)
    if not tipo_activo:
        return None, []

    campos = list(
        CampoTipoActivo.objects.filter(
            tipo_activo=tipo_activo,
            is_active=True
        ).order_by('orden', 'nombre', 'id')
    )
    return tipo_activo, campos


class ActivoListView(LoginRequiredMixin, TemplateView):
    template_name = 'gestion_tic/activos/activo_list.html'

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        user_est = getattr(request.user, 'establecimiento', None)
        tipo_id = request.POST.get('tipo') or request.GET.get('tipo')
        tipo_activo, campos = _get_campos_for_tipo(tipo_id, user_est)

        if action == 'get_columns':
            columns_data = [
                {
                    'id': c.id,
                    'nombre': c.nombre,
                    'tipo_campo': c.tipo_campo,
                    'orden': c.orden,
                }
                for c in campos
            ]
            return JsonResponse({
                'success': True,
                'tipo_id': tipo_activo.id if tipo_activo else None,
                'columns': columns_data
            })

        if action != 'search':
            return JsonResponse({'error': 'Acción no válida'}, status=400)

        draw = _as_int(request.POST.get('draw', 1), 1)
        start = max(0, _as_int(request.POST.get('start', 0), 0))
        length = _as_int(request.POST.get('length', 10), 10)

        if user_est:
            queryset = Activo.objects.filter(
                establecimiento=user_est,
                is_active=True
            )
        else:
            queryset = Activo.objects.filter(is_active=True)

        records_total = queryset.count()

        # Filtros específicos
        if tipo_id:
            if tipo_activo:
                queryset = queryset.filter(tipo=tipo_activo)
            else:
                queryset = queryset.none()

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
            search_q = (
                    Q(codigo_barra__icontains=search) |
                    Q(serie__icontains=search) |
                    Q(tipo__nombre__icontains=search) |
                    Q(marca__nombre__icontains=search) |
                    Q(modelo__nombre__icontains=search) |
                    Q(contrato__nombre__icontains=search) |
                    Q(observacion__icontains=search)
            )

            carac_filter = Q(valor__icontains=search)
            search_lower = search.lower()
            if search_lower in ('si', 'sí', 's'):
                carac_filter |= Q(campo__tipo_campo='boolean', valor__in=['True', 'true', '1', 'si', 'sí', 'Si', 'Sí'])
            elif search_lower in ('no', 'n'):
                carac_filter |= Q(campo__tipo_campo='boolean', valor__in=['False', 'false', '0', 'no', 'No'])

            date_parts = search.split('/')
            if len(date_parts) == 3:
                d, m, y = date_parts
                if d.isdigit() and m.isdigit() and y.isdigit():
                    iso_date = f"{y.zfill(4)}-{m.zfill(2)}-{d.zfill(2)}"
                    carac_filter |= Q(campo__tipo_campo='date', valor__icontains=iso_date)

            carac_subquery = ActivoCaracteristica.objects.filter(
                activo=OuterRef('pk'),
                campo__is_active=True
            ).filter(carac_filter)

            if tipo_activo:
                carac_subquery = carac_subquery.filter(campo__tipo_activo=tipo_activo)

            search_q |= Q(Exists(carac_subquery))
            queryset = queryset.filter(search_q)

        # Ordenamiento
        order_index = _as_int(request.POST.get('order[0][column]'), 1)
        order_dir = request.POST.get('order[0][dir]', 'asc').lower()
        col_data = request.POST.get(f'columns[{order_index}][data]', '')

        target_campo = None
        campos_by_id = {c.id: c for c in campos}
        if col_data and col_data.startswith('caracteristica_'):
            campo_id = _as_int(col_data.replace('caracteristica_', ''))
            target_campo = campos_by_id.get(campo_id)
        elif order_index >= 5 and (order_index - 5) < len(campos):
            target_campo = campos[order_index - 5]

        if target_campo:
            subquery_val = ActivoCaracteristica.objects.filter(
                activo=OuterRef('pk'),
                campo=target_campo
            ).values('valor')[:1]

            if target_campo.tipo_campo == 'number':
                dyn_val = NullIf(Subquery(subquery_val), Value(''))
                queryset = queryset.annotate(dyn_sort=Cast(dyn_val, output_field=FloatField()))
            elif target_campo.tipo_campo == 'date':
                dyn_val = NullIf(Subquery(subquery_val), Value(''))
                queryset = queryset.annotate(dyn_sort=Cast(dyn_val, output_field=DateField()))
            elif target_campo.tipo_campo == 'boolean':
                dyn_val = Subquery(subquery_val)
                queryset = queryset.annotate(
                    dyn_sort=Case(
                        When(dyn_val__in=['True', 'true', '1', 'si', 'sí', 'Si', 'Sí'], then=Value(1)),
                        When(dyn_val__in=['False', 'false', '0', 'no', 'No'], then=Value(0)),
                        default=Value(None),
                        output_field=IntegerField()
                    )
                )
            else:
                dyn_val = NullIf(Subquery(subquery_val), Value(''))
                queryset = queryset.annotate(dyn_sort=dyn_val)

            if order_dir == 'desc':
                queryset = queryset.order_by(F('dyn_sort').desc(nulls_last=True), '-pk')
            else:
                queryset = queryset.order_by(F('dyn_sort').asc(nulls_last=True), 'pk')
        else:
            columnas_estaticas = {
                0: 'id',
                1: 'codigo_barra',
                2: 'tipo__nombre',
                3: 'marca__nombre',
                4: 'contrato__nombre',
            }
            if col_data == 'id':
                campo_orden = 'id'
            elif col_data == 'codigo_barra':
                campo_orden = 'codigo_barra'
            elif col_data == 'tipo':
                campo_orden = 'tipo__nombre'
            elif col_data == 'marca_modelo':
                campo_orden = 'marca__nombre'
            elif col_data == 'contrato':
                campo_orden = 'contrato__nombre'
            else:
                campo_orden = columnas_estaticas.get(order_index, 'codigo_barra')

            if order_dir == 'desc':
                campo_orden = f'-{campo_orden}'
            queryset = queryset.order_by(campo_orden, 'pk')

        queryset = queryset.select_related('tipo', 'marca', 'modelo', 'contrato').prefetch_related('movimientos')
        records_filtered = queryset.count()

        if length != -1:
            queryset = queryset[start:start + length]

        page_activos = list(queryset)
        activo_ids = [obj.id for obj in page_activos]
        carac_map = {}
        if campos and activo_ids:
            caracs = ActivoCaracteristica.objects.filter(
                activo_id__in=activo_ids,
                campo__in=campos
            ).select_related('campo')
            for c in caracs:
                if c.activo_id not in carac_map:
                    carac_map[c.activo_id] = {}
                carac_map[c.activo_id][c.campo_id] = c.valor

        data = []
        for obj in page_activos:
            ultimo_mov = obj.movimientos.first()
            acta_url = reverse('gestion_tic:activo_acta_pdf', kwargs={'pk': ultimo_mov.pk}) if ultimo_mov else None
            row_dict = {
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
            }
            if campos:
                for campo in campos:
                    raw_val = carac_map.get(obj.id, {}).get(campo.id)
                    row_dict[f'caracteristica_{campo.id}'] = _format_caracteristica_value(raw_val, campo.tipo_campo)

            data.append(row_dict)

        columns_meta = [
            {
                'id': c.id,
                'nombre': c.nombre,
                'tipo_campo': c.tipo_campo,
                'orden': c.orden,
            }
            for c in campos
        ]

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
            'columns': columns_meta,
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Activos'
        context['resource_type'] = 'activo'
        context['create_url'] = reverse_lazy('gestion_tic:activo_create')
        context['edit_url_template'] = reverse_lazy('gestion_tic:activo_update', kwargs={'pk': 0})
        context['delete_url_template'] = reverse_lazy('gestion_tic:activo_deactivate', kwargs={'pk': 0})

        tipo_id = self.request.GET.get('tipo')
        establecimiento = getattr(self.request.user, 'establecimiento', None)
        tipo_activo, campos = _get_campos_for_tipo(tipo_id, establecimiento)
        context['tipo_id'] = str(tipo_activo.id) if tipo_activo else ''

        if establecimiento:
            context['tipos_activos'] = TipoActivo.objects.filter(establecimiento=establecimiento, is_active=True)
        else:
            context['tipos_activos'] = TipoActivo.objects.filter(is_active=True)

        context['dynamic_columns'] = [
            {
                'id': c.id,
                'nombre': c.nombre,
                'tipo_campo': c.tipo_campo,
                'orden': c.orden,
            }
            for c in campos
        ]
        return context


class ActivoCreateView(LoginRequiredMixin, CreateView):
    model = Activo
    form_class = ActivoForm
    template_name = 'gestion_tic/activos/activo_form.html'
    title = 'Crear Activo'

    def dispatch(self, request, *args, **kwargs):
        user_est = getattr(request.user, 'establecimiento', None)
        tipo_id = request.GET.get('tipo')
        self.tipo_activo = _get_tipo_activo_or_404(tipo_id, user_est)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        tipo_id = self.request.GET.get('tipo') or self.request.POST.get('tipo')
        user_est = getattr(self.request.user, 'establecimiento', None)
        tipo_activo = self.tipo_activo or _get_tipo_activo_or_404(tipo_id, user_est)
        if tipo_activo:
            kwargs['tipo_activo'] = tipo_activo
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

    def get_success_url(self):
        tipo_id = self.object.tipo_id or (self.tipo_activo.id if self.tipo_activo else None)
        if tipo_id:
            return f"{reverse('gestion_tic:activo_create')}?tipo={tipo_id}"
        return reverse('gestion_tic:activo_create')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipo_activo'] = self.tipo_activo
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            context['tipos_activos'] = TipoActivo.objects.filter(
                establecimiento=self.request.user.establecimiento,
                is_active=True
            )
        else:
            context['tipos_activos'] = TipoActivo.objects.filter(is_active=True)
        context['title'] = self.title
        context['submit_label'] = 'Guardar Activo'

        list_url = reverse('gestion_tic:activo_list')
        if self.tipo_activo:
            list_url = f"{list_url}?tipo={self.tipo_activo.id}"
        context['list_url'] = list_url
        return context


class ActivoUpdateView(LoginRequiredMixin, UpdateView):
    model = Activo
    form_class = ActivoForm
    template_name = 'gestion_tic/activos/activo_form.html'
    title = 'Editar Activo'

    def dispatch(self, request, *args, **kwargs):
        user_est = getattr(request.user, 'establecimiento', None)
        tipo_id = request.GET.get('tipo')
        if tipo_id:
            _get_tipo_activo_or_404(tipo_id, user_est)
        return super().dispatch(request, *args, **kwargs)

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

    def get_success_url(self):
        tipo_id = self.object.tipo_id
        if tipo_id:
            return f"{reverse('gestion_tic:activo_update', kwargs={'pk': self.object.pk})}?tipo={tipo_id}"
        return reverse('gestion_tic:activo_update', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activo'] = self.object
        context['tipo_activo'] = self.object.tipo
        context['title'] = f'Editar Activo: {self.object.codigo_barra}'
        context['submit_label'] = 'Actualizar Activo'

        list_url = reverse('gestion_tic:activo_list')
        if self.object.tipo_id:
            list_url = f"{list_url}?tipo={self.object.tipo_id}"
        context['list_url'] = list_url
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
    ).order_by('-created_at', '-id')

    # Regla de asignación:
    # 1. Si requiere recepción conforme, DEBE estar recepcionado (recepcionado=True)
    # 2. Si no requiere recepción, debe ser asignación o tener funcionario asignado (histórico)
    condicion_asignado = (
            (Q(tipo_movimiento__requiere_recepcion=True) & Q(recepcionado=True)) |
            (Q(tipo_movimiento__requiere_recepcion=False) & (
                    Q(tipo_movimiento__es_asignacion=True) | Q(funcionario__isnull=False)))
    )

    queryset = (
        MovimientoActivo.objects
        .filter(
            id=Subquery(ultimo_movimiento.values('id')[:1]),
            activo__is_active=True,
            activo__de_baja=False
        )
        .filter(condicion_asignado)
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
                Q(nombre_completo__icontains=search) |
                Q(departamento__icontains=search) |
                Q(unidad_organizacional__nombre__icontains=search) |
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
            'unidad_organizacional', 'unidad_organizacional__padre',
            'ip', 'tipo_movimiento'
        ).order_by(campo, 'pk')

        records_filtered = queryset.count()

        if length != -1:
            queryset = queryset[start:start + length]

        data = []
        for mov in queryset:
            func_nombre = '-'
            if mov.nombre_completo:
                func_nombre = mov.nombre_completo
            elif mov.funcionario:
                if hasattr(mov.funcionario, 'nombre') and mov.funcionario.nombre:
                    func_nombre = mov.funcionario.nombre
                else:
                    parts = [mov.funcionario.nombres or '', mov.funcionario.apellidos or '']
                    func_nombre = ' '.join(p for p in parts if p).strip() or '-'

            unidad_nombre = '-'
            unidad_padre = ''
            if mov.departamento:
                unidad_nombre = mov.departamento
                if mov.unidad_organizacional and mov.unidad_organizacional.padre:
                    unidad_padre = mov.unidad_organizacional.padre.nombre or ''
            elif mov.unidad_organizacional:
                unidad_nombre = mov.unidad_organizacional.nombre or '-'
                if mov.unidad_organizacional.padre:
                    unidad_padre = mov.unidad_organizacional.padre.nombre or ''
            elif mov.funcionario and mov.funcionario.unidad_organizacional:
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
