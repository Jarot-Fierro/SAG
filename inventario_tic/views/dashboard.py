from collections import Counter
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from ..models import AsignacionEstacion, Celular, Computador, Monitor, Producto, ProductoAsignadoEstacion
from ..models.mantenedores import Establecimiento


def scoped(model, user, field='establecimiento_id'):
    qs = model.objects.all()
    if not user.is_superuser:
        qs = qs.filter(**{field: user.establecimiento_id}) if user.establecimiento_id else qs.none()
    return qs


def inicio_mes_anterior(fecha, meses):
    numero = fecha.year * 12 + fecha.month - 1 - meses
    return date(numero // 12, numero % 12 + 1, 1)


@login_required
@require_GET
def dashboard(request):
    hoy = timezone.localdate() if settings.USE_TZ else timezone.now().date()
    return render(request, 'inventario_tic/dashboard.html', {
        'title': 'Dashboard de Inventario TIC',
        'destinos': scoped(Establecimiento, request.user).filter(is_active=True).order_by('nombre'),
        'desde': inicio_mes_anterior(hoy, 11).isoformat(), 'hasta': hoy.isoformat(),
        'widgets': [('computadores', 'Computadores disponibles', 'bi-pc-display'),
                    ('monitores', 'Monitores disponibles', 'bi-display'),
                    ('celulares', 'Celulares disponibles', 'bi-phone'),
                    ('asignados', 'Equipos asignados', 'bi-person-check'),
                    ('stock_bajo', 'Productos con stock bajo', 'bi-exclamation-triangle'),
                    ('agotados', 'Productos agotados', 'bi-box-seam'),
                    ('funcionarios', 'Funcionarios con equipamiento', 'bi-people'),
                    ('entregas_mes', 'Entregas del mes actual', 'bi-truck')],
        'graficos': [('equipos', 'Asignados vs. disponibles por tipo', 'inventario'),
                     ('distribucion', 'Equipos asignados por establecimiento destino', 'inventario'),
                     ('reposicion', 'Productos que requieren reposición', 'stock'),
                     ('evolucion', 'Entregas de estaciones en el período', 'actividad'),
                     ('productos', 'Productos más entregados en el período', 'actividad')],
    })


def inventario(user, destino):
    disponibles = {}
    series = []
    distribucion = Counter()
    funcionarios = set()
    asignados = total = 0
    for model, nombre, clave in ((Computador, 'Computadores', 'computadores'),
                                  (Monitor, 'Monitores', 'monitores'), (Celular, 'Celulares', 'celulares')):
        base = scoped(model, user).filter(is_active=True)
        libre = base.filter(asignado=False, responsable__isnull=True).count()
        asignado = base.filter(asignado=True, responsable__isnull=False)
        if destino:
            asignado = asignado.filter(establecimiento_mantenedor_id=destino)
        cantidad = asignado.count()
        disponibles[clave] = libre
        series.append({'tipo': nombre, 'asignados': cantidad, 'disponibles': libre})
        asignados += cantidad
        total += base.count()
        funcionarios.update(asignado.values_list('responsable_id', flat=True))
        for fila in asignado.order_by().values('establecimiento_mantenedor__nombre').annotate(cantidad=Count('pk')):
            distribucion[fila['establecimiento_mantenedor__nombre'] or 'Sin destino'] += fila['cantidad']
    productos = scoped(ProductoAsignadoEstacion, user, 'asignacion__establecimiento_id')
    if destino:
        productos = productos.filter(asignacion__destino_id=destino)
    funcionarios.update(productos.values_list('asignacion__responsable_id', flat=True))
    return {'widgets': {**disponibles, 'asignados': asignados, 'funcionarios': len(funcionarios)},
            'porcentaje': round(asignados * 100 / total, 1) if total else 0,
            'equipos': series,
            'distribucion': [{'nombre': nombre, 'cantidad': cantidad} for nombre, cantidad in distribucion.most_common()]}


def stock(user):
    base = scoped(Producto, user).filter(is_active=True)
    bajos = base.filter(stock_disponible__lte=F('stock_minimo'))
    alertas = list(bajos.order_by('stock_disponible', 'nombre', 'pk').values(
        'nombre', 'stock_disponible', 'stock_minimo')[:10])
    return {'widgets': {'stock_bajo': bajos.count(), 'agotados': base.filter(stock_disponible=0).count()},
            'reposicion': alertas, 'alertas': alertas}


def actividad(user, destino, desde, hasta):
    base = scoped(AsignacionEstacion, user)
    if destino:
        base = base.filter(destino_id=destino)

    def limite(fecha):
        valor = datetime.combine(fecha, time.min)
        return timezone.make_aware(valor) if settings.USE_TZ else valor

    periodo = base.filter(created_at__gte=limite(desde), created_at__lt=limite(hasta + timedelta(days=1)))
    hoy = timezone.localdate() if settings.USE_TZ else timezone.now().date()
    mes = base.filter(created_at__gte=limite(hoy.replace(day=1)), created_at__lt=limite(hoy + timedelta(days=1))).count()
    meses = {fila['mes'].strftime('%Y-%m'): fila['cantidad'] for fila in periodo.order_by().annotate(
        mes=TruncMonth('created_at')).values('mes').annotate(cantidad=Count('pk'))}
    evolucion = []
    cursor = desde.replace(day=1)
    while cursor <= hasta:
        clave = cursor.strftime('%Y-%m')
        evolucion.append({'mes': clave, 'cantidad': meses.get(clave, 0)})
        cursor = inicio_mes_anterior(cursor, -1)
    productos = list(ProductoAsignadoEstacion.objects.filter(asignacion__in=periodo).order_by().values(
        'producto_id', 'producto__nombre').annotate(cantidad=Sum('cantidad')).order_by('-cantidad', 'producto_id')[:10])
    ultimas = []
    for entrega in periodo.order_by('-created_at', '-pk')[:10]:
        fecha = timezone.localtime(entrega.created_at) if timezone.is_aware(entrega.created_at) else entrega.created_at
        ultimas.append({'folio': entrega.pk, 'fecha': fecha.strftime('%d/%m/%Y %H:%M'),
                        'responsable': entrega.contenido.get('responsable', ''),
                        'destino': entrega.contenido.get('destino', ''),
                        'cantidad': sum(item.get('cantidad', 1) for item in entrega.contenido.get('items', []))})
    return {'widgets': {'entregas_mes': mes}, 'evolucion': evolucion, 'productos': productos, 'ultimas': ultimas}


@login_required
@require_GET
def datos(request):
    bloque = request.GET.get('bloque')
    if bloque not in ('inventario', 'stock', 'actividad'):
        return JsonResponse({'error': 'Bloque no válido.'}, status=400)
    destino = request.GET.get('destino', '').strip()
    if destino and (not destino.isdecimal() or len(destino) > 18 or not scoped(
            Establecimiento, request.user).filter(pk=destino, is_active=True).exists()):
        return JsonResponse({'error': 'Establecimiento destino no disponible.'}, status=400)
    try:
        desde = date.fromisoformat(request.GET.get('desde', ''))
        hasta = date.fromisoformat(request.GET.get('hasta', ''))
        if desde > hasta or (hasta - desde).days > 3660 or hasta.year > 9998:
            raise ValueError
    except ValueError:
        return JsonResponse({'error': 'Seleccione fechas válidas, en orden y con un máximo de diez años.'}, status=400)
    if bloque == 'inventario':
        resultado = inventario(request.user, destino)
    elif bloque == 'stock':
        resultado = stock(request.user)
    else:
        resultado = actividad(request.user, destino, desde, hasta)
    resultado['actualizado'] = timezone.now().isoformat()
    return JsonResponse(resultado)
