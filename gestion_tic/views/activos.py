from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Subquery
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from gestion_tic.forms.activos import ActivoForm
from gestion_tic.models import Activo, TipoActivo, MovimientoActivo


@login_required
def activo_list(request):
    tipo_id = request.GET.get('tipo')
    url_form = reverse('gestion_tic:activo_create')
    if tipo_id:
        activos = Activo.objects.filter(
            establecimiento=request.user.establecimiento, tipo=tipo_id
        ).select_related('tipo', 'marca', 'modelo')
        url_form = reverse('gestion_tic:activo_create') + f'?tipo={tipo_id}'
    else:
        activos = None

    return render(request, 'gestion_tic/activos/list_activos.html', {
        'activos': activos,
        'url_form': url_form,
        'title': 'Listado de Activos'
    })


@login_required
def activo_create(request):
    tipo_id = request.GET.get('tipo')
    tipo_activo = None
    url_list = f"{reverse('gestion_tic:activo_list')}?tipo={tipo_id}"
    if tipo_id:
        tipo_activo = get_object_or_404(TipoActivo, id=tipo_id)
        url_list = reverse('gestion_tic:activo_list') + f'?tipo={tipo_id}'

    if request.method == 'POST':
        # El tipo_activo puede venir del POST si el campo 'tipo' está habilitado, 
        # pero para seguridad lo tomamos de lo que definimos inicialmente.
        form = ActivoForm(request.POST, tipo_activo=tipo_activo)
        if form.is_valid():
            activo = form.save(commit=False)
            activo.establecimiento = request.user.establecimiento
            activo.save()
            form.save_dynamic_fields(activo)
            messages.success(request, 'Activo creado correctamente.')
            return redirect(url_list)
    else:
        form = ActivoForm(tipo_activo=tipo_activo)

    tipos_activos = TipoActivo.objects.all()

    return render(request, 'gestion_tic/activos/form_activos.html', {
        'form': form,
        'tipo_activo': tipo_activo,
        'tipos_activos': tipos_activos,
        'url_list': url_list,
        'title': 'Crear Activo'
    })


@login_required
def activo_edit(request, pk):
    activo = get_object_or_404(Activo, pk=pk, establecimiento=request.user.establecimiento)

    if request.method == 'POST':
        form = ActivoForm(request.POST, instance=activo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Activo actualizado correctamente.')
            return redirect('gestion_tic:activo_list')
    else:
        form = ActivoForm(instance=activo)

    return render(request, 'gestion_tic/activos/form_activos.html', {
        'form': form,
        'activo': activo,
        'tipo_activo': activo.tipo,
        'title': f'Editar Activo: {activo.codigo_barra}'
    })


@login_required
def activo_list_asignado(request):
    ultimo_movimiento = MovimientoActivo.objects.filter(
        activo=OuterRef('activo')
    ).order_by('-updated_at', '-id')

    movimientos_activos = (
        MovimientoActivo.objects
        .filter(
            id=Subquery(ultimo_movimiento.values('id')[:1]),
            establecimiento=request.user.establecimiento,
            funcionario__isnull=False
        )
        .select_related('activo', 'funcionario')
    )

    return render(request, 'gestion_tic/activos/activos_asignados.html', {
        'movimientos_activos': movimientos_activos,
        'title': 'Listado de Activos Asignados'
    })
