from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from gestion_tic.models import Activo


@login_required
def equipos_baja(request):
    # Obtener el carrito de la sesión
    # Guardamos los IDs como strings o ints, Django session maneja ambos pero seremos consistentes
    carrito = request.session.get('carrito_baja', [])

    if request.method == 'POST':
        action = request.POST.get('action')
        activo_id = request.POST.get('activo_id')

        if action == 'add' and activo_id:
            activo_id = int(activo_id)
            if activo_id not in carrito:
                # Verificar que el activo existe y pertenece al establecimiento
                activo = get_object_or_404(Activo, id=activo_id, establecimiento=request.user.establecimiento)
                if not activo.de_baja:
                    carrito.append(activo_id)
                    request.session['carrito_baja'] = carrito
                    messages.success(request, f'Equipo {activo.codigo_barra} añadido al carrito.')
                else:
                    messages.warning(request, 'El equipo ya está dado de baja.')
            else:
                messages.warning(request, 'El equipo ya está en el carrito.')

        elif action == 'remove' and activo_id:
            activo_id = int(activo_id)
            if activo_id in carrito:
                carrito.remove(activo_id)
                request.session['carrito_baja'] = carrito
                messages.success(request, 'Equipo quitado del carrito.')

        elif action == 'clear':
            request.session['carrito_baja'] = []
            messages.success(request, 'Carrito vaciado.')

        elif action == 'procesar':
            if not carrito:
                messages.error(request, 'El carrito está vacío.')
            else:
                # Realizar la baja masiva
                cantidad = Activo.objects.filter(
                    id__in=carrito,
                    establecimiento=request.user.establecimiento
                ).update(de_baja=True)

                request.session['carrito_baja'] = []
                messages.success(request, f'Se han dado de baja {cantidad} equipos correctamente.')
                return redirect('gestion_tic:activo_list')

        return redirect('gestion_tic:equipos_baja')

    # GET: Listar activos en el carrito
    activos_carrito = Activo.objects.filter(id__in=carrito).select_related('tipo', 'marca', 'modelo')

    # Activos disponibles para agregar (no están de baja y no están en el carrito)
    q = request.GET.get('q', '')
    activos_disponibles = Activo.objects.filter(
        establecimiento=request.user.establecimiento,
        de_baja=False
    ).exclude(id__in=carrito).select_related('tipo', 'marca', 'modelo')

    if q:
        activos_disponibles = activos_disponibles.filter(codigo_barra__icontains=q)

    return render(request, 'gestion_tic/activos/equipos_baja.html', {
        'activos_carrito': activos_carrito,
        'activos_disponibles': activos_disponibles,
        'q': q,
        'title': 'Baja Masiva de Equipos'
    })
