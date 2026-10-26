from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from gestion_tic.filters.activo import ActivoFormFilter
from gestion_tic.forms.movimientos import MovimientoActivoForm, RecepcionConformeForm
from gestion_tic.models import Activo, MovimientoActivo


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@login_required
def movimientos_busqueda(request):
    return render(request, 'gestion_tic/activos/movimiento_activo_busqueda.html')


@login_required
def movimientos_activo(request):
    title = 'Movimientos de Activo'
    establecimiento = getattr(request.user, 'establecimiento', None)
    activo = None
    movimientos = []
    ultimo_movimiento = None
    form_movimiento = None
    query = request.GET.get('q')

    if query:
        filter_kwargs = {'codigo_barra': query}
        if establecimiento:
            filter_kwargs['establecimiento'] = establecimiento

        activo = (
            Activo.objects
            .select_related('tipo', 'marca', 'modelo')
            .filter(**filter_kwargs)
            .first()
        )

        if activo is None:
            messages.error(
                request,
                f"No se encontró un activo con el código de barra '{query}'."
            )
            return redirect('gestion_tic:movimientos_busqueda')

        if not activo.is_active or activo.de_baja:
            messages.warning(
                request,
                f"El equipo con código o serie '{query}' se encuentra dado de baja."
            )
            return redirect('gestion_tic:movimientos_busqueda')

        movimientos = activo.movimientos.all().select_related(
            'tipo_movimiento', 'funcionario', 'unidad_organizacional', 'ip'
        ).order_by('-created_at')
        ultimo_movimiento = movimientos.first()

        if request.method == 'POST' and 'tipo_movimiento' in request.POST:
            form_movimiento = MovimientoActivoForm(request.POST, establecimiento=establecimiento)
            if form_movimiento.is_valid():
                nuevo_mov = form_movimiento.save(commit=False)
                nuevo_mov.activo = activo
                if establecimiento:
                    nuevo_mov.establecimiento = establecimiento
                if nuevo_mov.funcionario:
                    nuevo_mov.unidad_organizacional = nuevo_mov.funcionario.unidad_organizacional

                if nuevo_mov.ip:
                    nuevo_mov.ip.asignado = True
                    nuevo_mov.ip.save()
                nuevo_mov.save()
                messages.success(request, "Movimiento registrado correctamente.")
                return redirect(f"{request.path}?q={query}")
        else:
            initial_data = {}
            if ultimo_movimiento:
                initial_data = {
                    'funcionario': ultimo_movimiento.funcionario,
                    'ip': ultimo_movimiento.ip,
                }
            form_movimiento = MovimientoActivoForm(establecimiento=establecimiento, initial=initial_data)

    return render(request, 'gestion_tic/activos/movimientos_activo.html', {
        'title': title,
        'activo': activo,
        'movimientos': movimientos,
        'ultimo_movimiento': ultimo_movimiento,
        'form_movimiento': form_movimiento,
        'query': query,
    })


@login_required
def movimientos_activo_list(request):
    title = 'Movimientos de Activo'
    establecimiento = getattr(request.user, 'establecimiento', None)

    # Procesamiento DataTables Server-Side (action=search)
    action = request.POST.get('action') or request.GET.get('action')
    if action == 'search':
        draw = _as_int(request.POST.get('draw') or request.GET.get('draw'), 1)
        start = max(0, _as_int(request.POST.get('start') or request.GET.get('start'), 0))
        length = _as_int(request.POST.get('length') or request.GET.get('length'), 10)

        queryset = Activo.objects.filter(is_active=True, de_baja=False)
        if establecimiento:
            queryset = queryset.filter(establecimiento=establecimiento)

        records_total = queryset.count()

        # Filtros
        req_params = request.POST if request.method == 'POST' else request.GET

        tipo_id = req_params.get('tipo')
        if tipo_id:
            queryset = queryset.filter(tipo_id=tipo_id)

        marca_id = req_params.get('marca')
        if marca_id:
            queryset = queryset.filter(marca_id=marca_id)

        modelo_id = req_params.get('modelo')
        if modelo_id:
            queryset = queryset.filter(modelo_id=modelo_id)

        contrato_id = req_params.get('contrato')
        if contrato_id:
            queryset = queryset.filter(contrato_id=contrato_id)

        serie = req_params.get('serie', '').strip()
        if serie:
            queryset = queryset.filter(serie__icontains=serie)

        codigo_barra = req_params.get('codigo_barra', '').strip()
        if codigo_barra:
            queryset = queryset.filter(codigo_barra__icontains=codigo_barra)

        search = req_params.get('search[value]', '').strip()
        if search:
            queryset = queryset.filter(
                Q(codigo_barra__icontains=search) |
                Q(serie__icontains=search) |
                Q(tipo__nombre__icontains=search) |
                Q(marca__nombre__icontains=search) |
                Q(modelo__nombre__icontains=search) |
                Q(contrato__nombre__icontains=search)
            )

        columnas = {
            0: 'id',
            1: 'codigo_barra',
            2: 'tipo__nombre',
            3: 'marca__nombre',
            4: 'serie',
            5: 'contrato__nombre',
        }

        order_index = _as_int(req_params.get('order[0][column]'), 1)
        order_dir = req_params.get('order[0][dir]', 'asc')
        campo = columnas.get(order_index, 'codigo_barra')
        if order_dir == 'desc':
            campo = f'-{campo}'

        queryset = queryset.select_related('tipo', 'marca', 'modelo', 'contrato').order_by(campo, 'pk')
        records_filtered = queryset.count()

        if length != -1:
            queryset = queryset[start:start + length]

        data = []
        for a in queryset:
            data.append({
                'id': a.id,
                'codigo_barra': a.codigo_barra,
                'tipo': a.tipo.nombre if a.tipo else '-',
                'marca_modelo': f"{a.marca.nombre if a.marca else '-'} / {a.modelo.nombre if a.modelo else '-'}",
                'serie': a.serie or '-',
                'contrato': a.contrato.nombre if a.contrato else '-',
                'consultar_url': f"{reverse('gestion_tic:movimientos_activo_list')}?q={a.codigo_barra}",
                'edit_url': reverse('gestion_tic:activo_update', kwargs={'pk': a.pk}),
            })

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })

    activo = None
    movimientos = []
    ultimo_movimiento = None
    form_movimiento = None
    query = request.GET.get('q', '').strip()
    filter_form = ActivoFormFilter(request.GET or None, establecimiento=establecimiento)

    if query:
        activo_filter = Q(codigo_barra=query) | Q(serie=query)
        activo_qs = Activo.objects.filter(activo_filter)
        if establecimiento:
            activo_qs = activo_qs.filter(establecimiento=establecimiento)
        activo = activo_qs.select_related('tipo', 'marca', 'modelo').first()

        if activo:
            if not activo.is_active or activo.de_baja:
                messages.warning(
                    request,
                    f"El equipo con código o serie '{query}' se encuentra dado de baja o inactivo."
                )
            else:
                movimientos = activo.movimientos.all().select_related(
                    'tipo_movimiento', 'funcionario', 'unidad_organizacional', 'ip'
                ).order_by('-created_at')
                ultimo_movimiento = movimientos.first()

                if request.method == 'POST' and 'tipo_movimiento' in request.POST:
                    form_movimiento = MovimientoActivoForm(request.POST, establecimiento=establecimiento)
                    if form_movimiento.is_valid():
                        nuevo_mov = form_movimiento.save(commit=False)
                        nuevo_mov.activo = activo
                        if establecimiento:
                            nuevo_mov.establecimiento = establecimiento
                        if nuevo_mov.funcionario:
                            nuevo_mov.unidad_organizacional = nuevo_mov.funcionario.unidad_organizacional

                        if nuevo_mov.ip:
                            nuevo_mov.ip.asignado = True
                            nuevo_mov.ip.save()
                        nuevo_mov.save()
                        messages.success(request, "Movimiento registrado correctamente.")
                        return redirect(f"{request.path}?q={query}")
                else:
                    initial_data = {}
                    if ultimo_movimiento:
                        initial_data = {
                            'funcionario': ultimo_movimiento.funcionario,
                            'ip': ultimo_movimiento.ip,
                        }
                    form_movimiento = MovimientoActivoForm(establecimiento=establecimiento, initial=initial_data)
        else:
            messages.warning(
                request,
                f"El equipo con código o serie '{query}' no existe. Debe ingresarlo primero para realizar operaciones con él en 'Equipos'."
            )

    return render(request, 'gestion_tic/activos/movimientos_activo_list.html', {
        'title': title,
        'activo': activo,
        'movimientos': movimientos,
        'ultimo_movimiento': ultimo_movimiento,
        'form_movimiento': form_movimiento,
        'query': query,
        'q': query,
        'filter_form': filter_form,
    })


@login_required
def recepcion_conforme(request, pk):
    title = 'Recepción Conforme'
    establecimiento = getattr(request.user, 'establecimiento', None)
    filter_kwargs = {'pk': pk}
    if establecimiento:
        filter_kwargs['establecimiento'] = establecimiento
    movimiento = get_object_or_404(MovimientoActivo, **filter_kwargs)

    if request.method == 'POST':
        form = RecepcionConformeForm(request.POST, instance=movimiento, establecimiento=establecimiento)
        if form.is_valid():
            movimiento = form.save(commit=False)
            movimiento.recepcionado = True
            movimiento.save()
            messages.success(request, "Recepción conforme registrada exitosamente.")
            return redirect('gestion_tic:movimientos_activo_list')
    else:
        form = RecepcionConformeForm(instance=movimiento, establecimiento=establecimiento)

    return render(request, 'gestion_tic/activos/recepcion_conforme.html', {
        'title': title,
        'movimiento': movimiento,
        'form': form,
    })
