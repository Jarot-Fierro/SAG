from django.contrib.auth.decorators import login_required
from django.db.models import Case, CharField, Count, F, IntegerField, Min, Q, Sum, Value, When
from django.db.models.functions import Coalesce, Concat, Trim
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from ..models import Celular, Computador, Monitor, ProductoAsignadoEstacion


COLUMNAS = ('col_funcionario', 'col_destino', 'col_tipo', 'col_descripcion',
            'col_inventario', 'col_serie', 'col_cantidad')


def filas_asignadas(user, search=''):
    consultas = []
    for model, tipo in ((Celular, 'Celular'), (Monitor, 'Monitor'), (Computador, 'Computador')):
        qs = model.objects.filter(is_active=True, asignado=True, responsable__isnull=False).order_by()
        if not user.is_superuser:
            qs = qs.filter(establecimiento_id=user.establecimiento_id) if user.establecimiento_id else qs.none()
        consultas.append(qs.annotate(
            col_funcionario=F('responsable__nombre'),
            col_destino=Coalesce('establecimiento_mantenedor__nombre', Value('—')),
            col_tipo=Value(tipo, output_field=CharField()),
            col_descripcion=Trim(Concat('marca__nombre', Value(' '), 'modelo__nombre')),
            col_inventario=Value('—', output_field=CharField()) if model is Celular else Coalesce('codigo_inventario', Value('—')),
            col_serie=F('imei' if model is Celular else 'numero_serie'),
            col_cantidad=Value(1, output_field=IntegerField()),
        ))

    productos = ProductoAsignadoEstacion.objects.order_by()
    if not user.is_superuser:
        productos = productos.filter(asignacion__establecimiento_id=user.establecimiento_id) if user.establecimiento_id else productos.none()
    # Una fila por funcionario y producto, incluso si hubo entregas a distintos destinos.
    productos = productos.values('asignacion__responsable_id', 'producto_id').annotate(
        destinos=Count('asignacion__destino_id', distinct=True),
        col_funcionario=F('asignacion__responsable__nombre'),
        col_destino=Case(
            When(destinos=1, then=Min('asignacion__destino__nombre')),
            default=Value('Varios establecimientos'), output_field=CharField(),
        ),
        col_tipo=Value('Producto', output_field=CharField()),
        col_descripcion=F('producto__nombre'),
        col_inventario=Value('—', output_field=CharField()),
        col_serie=Value('—', output_field=CharField()),
        col_cantidad=Sum('cantidad'),
    )
    consultas.append(productos)
    if search:
        filtros = Q()
        for campo in COLUMNAS[:-1]:
            filtros |= Q(**{f'{campo}__icontains': search})
        if search.isdecimal() and len(search) <= 9:
            filtros |= Q(col_cantidad=int(search))
        consultas = [qs.filter(filtros) for qs in consultas]
    return consultas[0].values(*COLUMNAS).union(*(qs.values(*COLUMNAS) for qs in consultas[1:]), all=True)


@login_required
@require_http_methods(['GET', 'POST'])
def listado(request):
    if request.method == 'GET':
        return render(request, 'inventario_tic/asignados_list.html', {'title': 'Equipamiento por funcionario'})
    if request.POST.get('action') != 'search':
        return JsonResponse({'error': 'Acción no válida.'}, status=400)

    def entero(campo, default):
        try:
            return int(request.POST.get(campo, default))
        except (TypeError, ValueError):
            return default

    total = filas_asignadas(request.user).count()
    search = request.POST.get('search[value]', '').strip()[:150]
    filas = filas_asignadas(request.user, search)
    filtrados = filas.count() if search else total
    index = entero('order[0][column]', 0)
    campo = COLUMNAS[index] if 0 <= index < len(COLUMNAS) else COLUMNAS[0]
    if request.POST.get('order[0][dir]') == 'desc':
        campo = f'-{campo}'
    filas = filas.order_by(campo, *COLUMNAS)
    start = max(0, entero('start', 0))
    length = entero('length', 10)
    if length != -1:
        filas = filas[start:start + (length if length > 0 else 10)]
    return JsonResponse({'draw': max(0, entero('draw', 1)), 'recordsTotal': total,
                         'recordsFiltered': filtrados, 'data': list(filas)})
