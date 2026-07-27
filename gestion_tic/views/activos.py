from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from gestion_tic.forms.activos import ActivoForm
from gestion_tic.models import Activo, TipoActivo


@login_required
def activo_list(request):
    tipo_id = request.GET.get('tipo')
    if tipo_id:
        activos = Activo.objects.filter(
            establecimiento=request.user.establecimiento, tipo=tipo_id
        ).select_related('tipo', 'marca', 'modelo')
    else:
        activos = None

    return render(request, 'gestion_tic/activos/list_activos.html', {
        'activos': activos,
        'title': 'Listado de Activos'
    })


@login_required
def activo_create(request):
    tipo_id = request.GET.get('tipo')
    tipo_activo = None
    if tipo_id:
        tipo_activo = get_object_or_404(TipoActivo, id=tipo_id)

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
            return redirect('gestion_tic:activo_list')
    else:
        form = ActivoForm(tipo_activo=tipo_activo)

    tipos_activos = TipoActivo.objects.all()

    return render(request, 'gestion_tic/activos/form_activos.html', {
        'form': form,
        'tipo_activo': tipo_activo,
        'tipos_activos': tipos_activos,
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
        'title': f'Editar Activo: {activo.numero_inventario}'
    })
