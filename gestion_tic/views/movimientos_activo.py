from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect

from gestion_tic.filters.activo import ActivoFormFilter
from gestion_tic.forms.movimientos import MovimientoActivoForm
from gestion_tic.models import Activo


@login_required
def movimientos_busqueda(request):
    return render(request, 'gestion_tic/activos/movimiento_activo_busqueda.html')


@login_required
def movimientos_activo(request):
    title = 'Movimientos de Activo'
    establecimiento = request.user.establecimiento
    activo = None
    movimientos = []
    ultimo_movimiento = None
    form_movimiento = None
    query = request.GET.get('q')

    if query:
        activo = Activo.objects.filter(
            Q(codigo_barra=query),
            establecimiento=establecimiento,
        ).select_related('tipo', 'marca', 'modelo').first()

        if not activo.is_active or activo.de_baja:
            messages.warning(
                request,
                f"El equipo con código o serie '{query}' se encuentra dado de baja."
            )
            return redirect('gestion_tic:movimientos_busqueda')

        if not activo:
            messages.warning(request,
                             f"El equipo con código o serie '{query}' no existe. Debe ingresarlo primero para realizar operaciones con él en 'Equipos'.")
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
    establecimiento = request.user.establecimiento
    activo = None
    movimientos = []
    ultimo_movimiento = None
    form_movimiento = None
    query = request.GET.get('q', '').strip()
    filter_form = ActivoFormFilter(request.GET or None, establecimiento=establecimiento)

    try:
        per_page = int(request.GET.get('per_page', 10))
        if per_page <= 0:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    list_activo = Activo.objects.filter(
        establecimiento=establecimiento,
        is_active=True
    ).select_related('tipo', 'marca', 'modelo', 'contrato').order_by('codigo_barra')

    if filter_form.is_valid():
        data = filter_form.cleaned_data
        if data.get('codigo_barra'):
            list_activo = list_activo.filter(codigo_barra__icontains=data['codigo_barra'])
        if data.get('tipo'):
            list_activo = list_activo.filter(tipo=data['tipo'])
        if data.get('marca'):
            list_activo = list_activo.filter(marca=data['marca'])
        if data.get('modelo'):
            list_activo = list_activo.filter(modelo=data['modelo'])
        if data.get('serie'):
            list_activo = list_activo.filter(serie__icontains=data['serie'])
        if data.get('contrato'):
            list_activo = list_activo.filter(contrato=data['contrato'])

    if query:
        activo = Activo.objects.filter(
            Q(codigo_barra=query) | Q(serie=query),
            establecimiento=establecimiento,
        ).select_related('tipo', 'marca', 'modelo').first()

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
                        nuevo_mov.establecimiento = establecimiento
                        if nuevo_mov.funcionario:
                            nuevo_mov.unidad_organizacional = nuevo_mov.funcionario.unidad_organizacional

                        if nuevo_mov.ip:
                            nuevo_mov.ip.asignado = True
                            nuevo_mov.ip.save()
                        nuevo_mov.save()
                        messages.success(request, "Movimiento registrado correctamente.")
                        return redirect(f"{request.path}?q={query}&per_page={per_page}")
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

        list_activo = list_activo.filter(
            Q(codigo_barra__icontains=query) |
            Q(serie__icontains=query) |
            Q(tipo__nombre__icontains=query) |
            Q(marca__nombre__icontains=query) |
            Q(modelo__nombre__icontains=query)
        )

    paginator = Paginator(list_activo, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'gestion_tic/activos/movimientos_activo_list.html', {
        'title': title,
        'activo': activo,
        'movimientos': movimientos,
        'ultimo_movimiento': ultimo_movimiento,
        'form_movimiento': form_movimiento,
        'query': query,
        'q': query,
        'list_activo': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
        'per_page': per_page,
        'filter_form': filter_form
    })
