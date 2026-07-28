from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect

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
            Q(codigo_barra=query) | Q(serie=query),
            establecimiento=establecimiento
        ).select_related('tipo', 'marca', 'modelo').first()

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
