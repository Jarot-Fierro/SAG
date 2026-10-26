from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from gestion_tic.filters.activo import ActivoFormFilter
from gestion_tic.models import Activo


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@login_required
def equipos_baja(request):
    establecimiento = getattr(request.user, 'establecimiento', None)
    carrito = request.session.get('carrito_baja', [])

    is_ajax = (
            request.headers.get('x-requested-with') == 'XMLHttpRequest' or
            request.POST.get('is_ajax') == 'true' or
            request.GET.get('is_ajax') == 'true'
    )

    action = request.POST.get('action') or request.GET.get('action')

    # DataTables Server-Side Search
    if action == 'search':
        draw = _as_int(request.POST.get('draw') or request.GET.get('draw'), 1)
        start = max(0, _as_int(request.POST.get('start') or request.GET.get('start'), 0))
        length = _as_int(request.POST.get('length') or request.GET.get('length'), 10)

        queryset = Activo.objects.filter(is_active=True, de_baja=False).exclude(id__in=carrito)
        if establecimiento:
            queryset = queryset.filter(establecimiento=establecimiento)

        records_total = queryset.count()

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
            })

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })

    if request.method == 'POST':
        activo_id = request.POST.get('activo_id')

        if action == 'add' and activo_id:
            activo_id = int(activo_id)
            if activo_id not in carrito:
                filter_kwargs = {'id': activo_id, 'is_active': True}
                if establecimiento:
                    filter_kwargs['establecimiento'] = establecimiento
                activo = get_object_or_404(Activo, **filter_kwargs)
                if not activo.de_baja:
                    carrito.append(activo_id)
                    request.session['carrito_baja'] = carrito
                    msg = f'Equipo {activo.codigo_barra} añadido al carrito.'
                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'message': msg,
                            'cart_count': len(carrito),
                            'item': {
                                'id': activo.id,
                                'codigo_barra': activo.codigo_barra,
                                'tipo_marca': f"{activo.tipo.nombre if activo.tipo else '-'} / {activo.marca.nombre if activo.marca else '-'}",
                            }
                        })
                    messages.success(request, msg)
                else:
                    if is_ajax:
                        return JsonResponse({'success': False, 'message': 'El equipo ya está dado de baja.'},
                                            status=400)
                    messages.warning(request, 'El equipo ya está dado de baja.')
            else:
                if is_ajax:
                    return JsonResponse({'success': False, 'message': 'El equipo ya está en el carrito.'}, status=400)
                messages.warning(request, 'El equipo ya está en el carrito.')

        elif action == 'remove' and activo_id:
            activo_id = int(activo_id)
            if activo_id in carrito:
                carrito.remove(activo_id)
                request.session['carrito_baja'] = carrito
                msg = 'Equipo quitado del carrito.'
                if is_ajax:
                    return JsonResponse({'success': True, 'message': msg, 'cart_count': len(carrito)})
                messages.success(request, msg)

        elif action == 'clear':
            request.session['carrito_baja'] = []
            msg = 'Carrito vaciado.'
            if is_ajax:
                return JsonResponse({'success': True, 'message': msg, 'cart_count': 0})
            messages.success(request, msg)

        elif action == 'procesar':
            if not carrito:
                if is_ajax:
                    return JsonResponse({'success': False, 'message': 'El carrito está vacío.'}, status=400)
                messages.error(request, 'El carrito está vacío.')
            else:
                update_kwargs = {'id__in': carrito}
                if establecimiento:
                    update_kwargs['establecimiento'] = establecimiento
                cantidad = Activo.objects.filter(**update_kwargs).update(de_baja=True)

                request.session['carrito_baja'] = []
                msg = f'Se han dado de baja {cantidad} equipos correctamente.'
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': msg,
                        'redirect_url': reverse('gestion_tic:activo_list')
                    })
                messages.success(request, msg)
                return redirect('gestion_tic:activo_list')

        if is_ajax:
            return JsonResponse({'success': True, 'cart_count': len(request.session.get('carrito_baja', []))})
        return redirect('gestion_tic:equipos_baja')

    # GET: Listar activos en el carrito
    activos_carrito = Activo.objects.filter(id__in=carrito).select_related('tipo', 'marca', 'modelo')
    filter_form = ActivoFormFilter(request.GET or None, establecimiento=establecimiento)

    return render(request, 'gestion_tic/activos/equipos_baja.html', {
        'activos_carrito': activos_carrito,
        'title': 'Baja Masiva de Equipos',
        'filter_form': filter_form,
        'url_action': reverse('gestion_tic:equipos_baja'),
    })
