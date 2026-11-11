from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from weasyprint import HTML

from gestion_tic.entregas import confirmar_entrega, recepcionar_entrega, validar_disponibilidad, \
    puede_recepcionar_entrega
from gestion_tic.forms.entregas import EntregaForm, DetalleForm, AccesoriosFormSet
from gestion_tic.models import EntregaActivos, DetalleEntrega, Activo


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def puede_gestionar(user):
    return user.has_perm('gestion_tic.add_movimientoactivo')


def disponibles(user):
    qs = EntregaActivos.objects.filter(establecimiento=user.establecimiento)
    if not puede_gestionar(user):
        qs = (qs.filter(funcionario_id=user.funcionario_id).exclude(estado='borrador')
              if user.funcionario_id else qs.none())
    return qs


def exigir_encargado(user):
    if not puede_gestionar(user) or not user.establecimiento_id:
        raise PermissionDenied('Se requiere permiso para registrar movimientos y un establecimiento.')


@login_required
def listado(request):
    if request.method == 'POST':
        if request.POST.get('action') != 'search':
            return JsonResponse({'error': 'Acción no válida'}, status=400)

        draw = _as_int(request.POST.get('draw'), 1)
        start = max(0, _as_int(request.POST.get('start'), 0))
        length = _as_int(request.POST.get('length'), 10)

        queryset = disponibles(request.user).select_related('funcionario')
        records_total = queryset.count()

        search = request.POST.get('search[value]', '').strip()
        if search:
            search_q = (
                    Q(funcionario__nombre__icontains=search) |
                    Q(funcionario__nombres__icontains=search) |
                    Q(funcionario__apellidos__icontains=search) |
                    Q(funcionario__rut__icontains=search) |
                    Q(estado__icontains=search) |
                    Q(observacion__icontains=search)
            )
            if search.isdigit():
                search_q |= Q(pk=int(search))

            search_lower = search.lower()
            if 'borrador' in search_lower:
                search_q |= Q(estado=EntregaActivos.Estado.BORRADOR)
            if 'pendiente' in search_lower or 'recepci' in search_lower:
                search_q |= Q(estado=EntregaActivos.Estado.PENDIENTE)
            if 'recepcionada' in search_lower:
                search_q |= Q(estado=EntregaActivos.Estado.RECEPCIONADA)

            queryset = queryset.filter(search_q)

        prefijo_estado = 'columns[2][columnControl][list]'
        estados = []
        for key, values in request.POST.lists():
            if key == prefijo_estado or key.startswith(prefijo_estado + '['):
                estados.extend(values)

        if estados:
            queryset = queryset.filter(estado__in=estados)

        columnas = {
            0: 'pk',
            1: 'funcionario__nombre',
            2: 'estado',
            3: 'created_at',
        }

        order_index = _as_int(request.POST.get('order[0][column]'), 0)
        order_dir = request.POST.get('order[0][dir]', 'desc')

        campo = columnas.get(order_index, 'pk')
        if order_dir == 'desc':
            campo = f'-{campo}'

        queryset = queryset.order_by(campo, '-pk')
        records_filtered = queryset.count()

        if length != -1:
            queryset = queryset[start:start + length]

        data = []
        for entrega in queryset:
            data.append({
                'id': entrega.pk,
                'folio': entrega.pk,
                'funcionario': str(entrega.funcionario) if entrega.funcionario else '-',
                'estado': entrega.estado,
                'estado_display': entrega.get_estado_display(),
                'created_at': entrega.created_at.strftime('%d/%m/%Y %H:%M') if entrega.created_at else '-',
                'detalle_url': reverse('gestion_tic:entrega_detalle', kwargs={'pk': entrega.pk}),
            })

        opciones_estados = [
            {'label': label, 'value': val}
            for val, label in EntregaActivos.Estado.choices
        ]

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
            'columnControl': {
                'estado': opciones_estados
            }
        })

    return render(request, 'gestion_tic/entregas/listado.html', {
        'title': 'Entregas de activos',
        'puede_gestionar': puede_gestionar(request.user),
    })


@login_required
def nueva(request):
    exigir_encargado(request.user)
    form = EntregaForm(request.POST or None, establecimiento=request.user.establecimiento)
    if request.method == 'POST' and form.is_valid():
        entrega = form.save(commit=False)
        entrega.establecimiento = request.user.establecimiento
        entrega.created_by = entrega.updated_by = request.user
        entrega.save()
        return redirect('gestion_tic:entrega_detalle', pk=entrega.pk)
    return render(request, 'gestion_tic/entregas/form.html', {'title': 'Nueva entrega', 'form': form})


@login_required
def detalle(request, pk):
    entrega = get_object_or_404(disponibles(request.user), pk=pk)
    form = EntregaForm(instance=entrega, establecimiento=entrega.establecimiento)
    if request.method == 'POST':
        accion = request.POST.get('accion')
        try:
            if accion == 'recepcionar':
                if request.POST.get('conforme') != 'si':
                    raise ValidationError('Debe confirmar la recepción de todos los activos.')
                recepcionar_entrega(entrega.pk, request.user)
                messages.success(request, 'Entrega completa recepcionada conforme.')
            else:
                exigir_encargado(request.user)
                with transaction.atomic():
                    entrega = EntregaActivos.objects.select_for_update().get(pk=entrega.pk)
                    if entrega.estado != EntregaActivos.Estado.BORRADOR:
                        raise ValidationError('Solo se puede modificar una entrega en borrador.')
                    if accion in ('guardar', 'confirmar'):
                        form = EntregaForm(request.POST, instance=entrega,
                                           establecimiento=entrega.establecimiento)
                        if not form.is_valid():
                            return render(request, 'gestion_tic/entregas/detalle.html',
                                          contexto(entrega, request.user, form))
                        form.instance.updated_by = request.user
                        form.save()
                        if accion == 'confirmar':
                            confirmar_entrega(entrega.pk, request.user)
                            messages.success(request, 'Entrega confirmada y pendiente de recepci\u00f3n.')
                    elif accion == 'quitar':
                        entrega.detalles.filter(pk=request.POST.get('detalle')).delete()
                    else:
                        raise ValidationError('Operación inválida.')
            return redirect('gestion_tic:entrega_detalle', pk=pk)
        except ValidationError as exc:
            messages.error(request, ' '.join(exc.messages))
            return redirect('gestion_tic:entrega_detalle', pk=pk)
    return render(request, 'gestion_tic/entregas/detalle.html', contexto(entrega, request.user, form))


def contexto(entrega, user, form):
    return {'title': f'Entrega #{entrega.pk}', 'entrega': entrega, 'form': form,
            'detalles': entrega.detalles.select_related('activo', 'activo__tipo', 'ip'),
            'puede_editar': puede_gestionar(user) and entrega.estado == 'borrador',
            'puede_recibir': puede_recepcionar_entrega(entrega, user) and entrega.estado == 'pendiente'}


@login_required
def item(request, pk, item_id=None):
    exigir_encargado(request.user)
    entrega = get_object_or_404(disponibles(request.user), pk=pk)
    instance = get_object_or_404(DetalleEntrega, entrega=entrega, pk=item_id) if item_id else None
    initial = [{'accesorio': a['id'], 'cantidad': a['cantidad'], 'observacion': a.get('observacion', '')}
               for a in instance.accesorios] if instance else []
    form = DetalleForm(request.POST or None, instance=instance, establecimiento=entrega.establecimiento)
    accesorios = AccesoriosFormSet(request.POST or None, initial=initial,
                                   form_kwargs={'establecimiento': entrega.establecimiento})
    if entrega.estado != 'borrador':
        messages.error(request, 'El carrito ya fue confirmado.')
        return redirect('gestion_tic:entrega_detalle', pk=pk)
    if request.method == 'POST' and form.is_valid() and accesorios.is_valid():
        try:
            with transaction.atomic():
                entrega = EntregaActivos.objects.select_for_update().get(pk=pk)
                if entrega.estado != 'borrador':
                    raise ValidationError('El carrito ya fue confirmado.')
                qs = Activo.objects.filter(establecimiento=entrega.establecimiento).filter(
                    Q(codigo_barra=form.cleaned_data['codigo']) | Q(serie=form.cleaned_data['codigo']))
                if instance:
                    qs = qs.filter(pk=instance.activo_id)
                encontrados = list(qs[:2])
                if len(encontrados) != 1:
                    raise ValidationError('No se encontró un activo único con ese código o serie.')
                activo = encontrados[0]
                validar_disponibilidad(activo)
                if entrega.detalles.filter(activo=activo).exclude(pk=instance.pk if instance else None).exists():
                    raise ValidationError('El activo ya está en el carrito.')
                if form.cleaned_data['ip'] and not activo.utiliza_ip:
                    raise ValidationError('Este activo no utiliza IP.')
                obj = form.save(commit=False)
                obj.entrega = entrega
                obj.activo = activo
                obj.accesorios = []
                ids = set()
                for fila in accesorios.cleaned_data:
                    acc = fila.get('accesorio')
                    if fila.get('DELETE') or not acc:
                        continue
                    if acc.pk in ids:
                        raise ValidationError('No repita un accesorio: ajuste su cantidad.')
                    ids.add(acc.pk)
                    obj.accesorios.append({'id': acc.pk, 'nombre': acc.nombre,
                                           'cantidad': fila['cantidad'], 'observacion': fila.get('observacion', '')})
                obj.save()
            return redirect('gestion_tic:entrega_detalle', pk=pk)
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(request, 'gestion_tic/entregas/item.html', {
        'title': 'Configurar activo', 'entrega': entrega, 'form': form, 'accesorios': accesorios})


@login_required
def acta(request, pk):
    entrega = get_object_or_404(disponibles(request.user), pk=pk)
    if entrega.estado == 'borrador':
        messages.error(request, 'Confirme la entrega antes de generar el acta.')
        return redirect('gestion_tic:entrega_detalle', pk=pk)
    html = render_to_string('gestion_tic/pdfs/entrega_acta.html', {
        'entrega': entrega, 'acta': entrega.snapshot_acta}, request=request)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="entrega_{pk}.pdf"'
    HTML(string=html, base_url=request.build_absolute_uri()).write_pdf(response)
    return response
