from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from core.models.unidad_organizacional import UnidadOrganizacional
from gestion_tic.filters.activo import ActivoFormFilter
from gestion_tic.forms.movimientos import MovimientoActivoForm, RecepcionConformeForm
from gestion_tic.models import Activo, MovimientoActivo, Accesorio, MovimientoActivoAccesorio


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _guardar_movimiento_con_accesorios(form_movimiento, activo, establecimiento, user, request_post,
                                       ultimo_movimiento=None):
    with transaction.atomic():
        nuevo_mov = form_movimiento.save(commit=False)
        nuevo_mov.activo = activo
        if establecimiento:
            nuevo_mov.establecimiento = establecimiento
        if user and user.is_authenticated:
            nuevo_mov.created_by = user
            nuevo_mov.updated_by = user

        # Estado inicial para entregas / movimientos
        nuevo_mov.recepcionado = False

        if nuevo_mov.funcionario:
            nuevo_mov.unidad_organizacional = nuevo_mov.funcionario.unidad_organizacional
            parts = [nuevo_mov.funcionario.nombres or '', nuevo_mov.funcionario.apellidos or '']
            func_nom = ' '.join(p for p in parts if p).strip()
            if not nuevo_mov.nombre_completo and func_nom:
                nuevo_mov.nombre_completo = func_nom
            if not nuevo_mov.departamento and nuevo_mov.unidad_organizacional:
                nuevo_mov.departamento = nuevo_mov.unidad_organizacional.nombre

        # Manejo consistente de IPs
        old_ip = ultimo_movimiento.ip if ultimo_movimiento else None
        if nuevo_mov.ip:
            if old_ip and old_ip != nuevo_mov.ip:
                old_ip.asignado = False
                old_ip.save()
            nuevo_mov.ip.asignado = True
            nuevo_mov.ip.save()
        elif old_ip:
            old_ip.asignado = False
            old_ip.save()

        nuevo_mov.save()

        # Guardar accesorios del movimiento
        acc_ids = request_post.getlist('accesorio_id[]') or request_post.getlist('accesorio_id')
        acc_cants = request_post.getlist('accesorio_cantidad[]') or request_post.getlist('accesorio_cantidad')
        acc_obss = request_post.getlist('accesorio_observacion[]') or request_post.getlist('accesorio_observacion')

        accesorios_procesados = set()
        for i, acc_id in enumerate(acc_ids):
            if not acc_id or acc_id in accesorios_procesados:
                continue
            accesorios_procesados.add(acc_id)

            try:
                acc_filter = {'pk': acc_id}
                if establecimiento:
                    acc_filter['establecimiento'] = establecimiento
                acc_obj = Accesorio.objects.filter(**acc_filter).first()
                if not acc_obj:
                    acc_obj = Accesorio.objects.get(pk=acc_id)
            except Accesorio.DoesNotExist:
                continue

            cant = 1
            if i < len(acc_cants):
                try:
                    cant = max(1, int(acc_cants[i]))
                except (ValueError, TypeError):
                    cant = 1

            obs = ''
            if i < len(acc_obss):
                obs = str(acc_obss[i])[:255]

            MovimientoActivoAccesorio.objects.create(
                movimiento=nuevo_mov,
                accesorio=acc_obj,
                nombre=acc_obj.nombre,
                cantidad=cant,
                observacion=obs,
                establecimiento=establecimiento,
                created_by=user if (user and user.is_authenticated) else None,
                updated_by=user if (user and user.is_authenticated) else None
            )

        return nuevo_mov


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

    accesorios_catalogo = Accesorio.objects.filter(is_active=True)
    if establecimiento:
        accesorios_catalogo = accesorios_catalogo.filter(establecimiento=establecimiento)
    accesorios_catalogo = accesorios_catalogo.order_by('nombre')

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
            'tipo_movimiento', 'funcionario', 'unidad_organizacional', 'ip', 'jefe_firmante'
        ).prefetch_related('accesorios').order_by('-created_at', '-id')
        ultimo_movimiento = movimientos.first()

        if request.method == 'POST' and 'tipo_movimiento' in request.POST:
            form_movimiento = MovimientoActivoForm(request.POST, establecimiento=establecimiento)
            if form_movimiento.is_valid():
                _guardar_movimiento_con_accesorios(
                    form_movimiento=form_movimiento,
                    activo=activo,
                    establecimiento=establecimiento,
                    user=request.user,
                    request_post=request.POST,
                    ultimo_movimiento=ultimo_movimiento
                )
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
        'accesorios_catalogo': accesorios_catalogo,
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

    accesorios_catalogo = Accesorio.objects.filter(is_active=True)
    if establecimiento:
        accesorios_catalogo = accesorios_catalogo.filter(establecimiento=establecimiento)
    accesorios_catalogo = accesorios_catalogo.order_by('nombre')

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
                    'tipo_movimiento', 'funcionario', 'unidad_organizacional', 'ip', 'jefe_firmante'
                ).prefetch_related('accesorios').order_by('-created_at', '-id')
                ultimo_movimiento = movimientos.first()

                if request.method == 'POST' and 'tipo_movimiento' in request.POST:
                    form_movimiento = MovimientoActivoForm(request.POST, establecimiento=establecimiento)
                    if form_movimiento.is_valid():
                        _guardar_movimiento_con_accesorios(
                            form_movimiento=form_movimiento,
                            activo=activo,
                            establecimiento=establecimiento,
                            user=request.user,
                            request_post=request.POST,
                            ultimo_movimiento=ultimo_movimiento
                        )
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
        'accesorios_catalogo': accesorios_catalogo,
    })


@login_required
def recepcion_conforme(request, pk):
    title = 'Recepción Conforme'
    establecimiento = getattr(request.user, 'establecimiento', None)
    filter_kwargs = {'pk': pk}
    if establecimiento:
        filter_kwargs['establecimiento'] = establecimiento

    movimiento = get_object_or_404(
        MovimientoActivo.objects.select_related(
            'activo', 'activo__tipo', 'activo__marca', 'activo__modelo', 'activo__establecimiento',
            'tipo_movimiento', 'jefe_firmante', 'ip'
        ).prefetch_related('accesorios'),
        **filter_kwargs
    )

    # 1. Validar que el tipo de movimiento requiera recepción conforme
    if not movimiento.tipo_movimiento.requiere_recepcion:
        messages.error(request, "Este tipo de movimiento no requiere recepción conforme.")
        return redirect('gestion_tic:movimientos_activo_list')

    # 2. Validar que no haya sido ya recepcionado
    if movimiento.recepcionado:
        messages.warning(request, "Este movimiento ya fue recepcionado conforme anteriormente.")
        return redirect('gestion_tic:movimientos_activo_list')

    # 3. Validar que no haya un movimiento posterior para el activo
    ultimo_mov_activo = movimiento.activo.movimientos.order_by('-created_at', '-id').first()
    if ultimo_mov_activo and ultimo_mov_activo.pk != movimiento.pk:
        messages.error(
            request,
            "No se puede confirmar la recepción: existe un movimiento posterior registrado para este equipo."
        )
        return redirect('gestion_tic:movimientos_activo_list')

    if request.method == 'POST':
        form = RecepcionConformeForm(request.POST, instance=movimiento, establecimiento=establecimiento)
        if form.is_valid():
            with transaction.atomic():
                mov_locked = MovimientoActivo.objects.select_for_update().get(pk=movimiento.pk)
                if mov_locked.recepcionado:
                    messages.warning(request, "Este movimiento ya fue recepcionado conforme.")
                    return redirect('gestion_tic:movimientos_activo_list')

                mov_locked.nombre_completo = form.cleaned_data['nombre_completo']
                depto = form.cleaned_data['departamento']
                if isinstance(depto, UnidadOrganizacional):
                    mov_locked.unidad_organizacional = depto
                    mov_locked.departamento = str(depto.nombre)
                else:
                    mov_locked.departamento = str(depto)

                mov_locked.recepcionado = True
                mov_locked.fecha_recepcion = timezone.now()
                mov_locked.recepcionado_por = request.user
                mov_locked.updated_by = request.user

                # Generar snapshot histórico del acta
                mov_locked.snapshot_acta = mov_locked.generar_snapshot_acta()
                mov_locked.save()

            messages.success(request, "Recepción conforme registrada exitosamente.")
            return redirect('gestion_tic:movimientos_activo_list')
    else:
        form = RecepcionConformeForm(instance=movimiento, establecimiento=establecimiento)

    return render(request, 'gestion_tic/activos/recepcion_conforme.html', {
        'title': title,
        'movimiento': movimiento,
        'form': form,
    })
