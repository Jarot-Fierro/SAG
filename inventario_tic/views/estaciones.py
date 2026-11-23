import base64
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q, F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from ..forms.estaciones import DestinoEstacionForm, seccion, visibles
from ..forms.mantenedores import FormFuncionarioInventario
from ..models import Computador, Monitor, Producto, Modelo, AsignacionEstacion, ProductoAsignadoEstacion


TIPOS = [('computador', 'Computador'), ('monitores', 'Monitores'), ('productos', 'Productos')]


def exigir_establecimiento(user):
    if not user.establecimiento_id:
        raise PermissionDenied('Debe tener un establecimiento asignado.')


@transaction.atomic
def guardar(request, destino, secciones):
    user = request.user
    datos = destino.cleaned_data
    contenido = {'destino': str(datos['establecimiento_mantenedor']),
                 'responsable': str(datos['responsable']), 'jefe': str(datos['jefe_entrega']),
                 'jefe_posicion': datos['jefe_entrega'].posicion, 'items': []}
    productos = []
    for tipo, _, formset, incluido in secciones:
        if not incluido:
            continue
        for fila in formset.forms:
            if not fila.ocupado:
                continue
            if fila.cleaned_data.get('nuevo'):
                obj = fila.registro.save(commit=False)
                obj.establecimiento_id = user.establecimiento_id
                obj.created_by = obj.updated_by = user
                obj.save()
            else:
                seleccionado = fila.cleaned_data['existente']
                obj = visibles(type(seleccionado), user).select_for_update().filter(pk=seleccionado.pk).first()
                if obj is None:
                    fila.add_error(None, 'El registro ya no está disponible.')
                    raise ValidationError('Revise los elementos seleccionados.')
            cantidad = fila.cleaned_data.get('cantidad', 1)
            if tipo == 'productos':
                actualizado = Producto.objects.filter(pk=obj.pk, stock_disponible__gte=cantidad).update(
                    stock_disponible=F('stock_disponible') - cantidad)
                if not actualizado:
                    fila.add_error('cantidad', f'Stock insuficiente para {obj.nombre}. Disponible: {obj.stock_disponible}.')
                    raise ValidationError('Revise las cantidades de productos.')
                obj.refresh_from_db()
                obj.updated_by = user
                obj.save()  # Mantener también la auditoría histórica del producto.
                productos.append((obj, cantidad))
            else:
                actualizado = type(obj).objects.filter(pk=obj.pk, asignado=False, responsable__isnull=True).update(asignado=True)
                if not actualizado:
                    fila.add_error('existente', 'El equipo ya no está disponible.')
                    raise ValidationError('Otro usuario asignó uno de los equipos. Seleccione otro.')
                obj.asignado = True
                for campo in ('establecimiento_mantenedor', 'responsable', 'jefe_entrega'):
                    setattr(obj, campo, datos[campo])
                obj.updated_by = user
                obj.save()
            contenido['items'].append({
                'tipo': tipo, 'id': obj.pk, 'descripcion': str(obj), 'cantidad': cantidad,
                'serie': getattr(obj, 'numero_serie', ''),
            })
    entrega = AsignacionEstacion.objects.create(
        establecimiento_id=user.establecimiento_id, destino=datos['establecimiento_mantenedor'],
        responsable=datos['responsable'], jefe_entrega=datos['jefe_entrega'], created_by=user, contenido=contenido)
    for producto, cantidad in productos:
        ProductoAsignadoEstacion.objects.create(asignacion=entrega, producto=producto, cantidad=cantidad)
    return entrega


@login_required
def nueva(request):
    exigir_establecimiento(request.user)
    data = request.POST if request.method == 'POST' else None
    destino = DestinoEstacionForm(data, request=request, prefix='destino')
    secciones = [(tipo, label, seccion(tipo, request.user, data if data is not None and data.get(f'incluir_{tipo}') == 'on' else None),
                  bool(data is not None and data.get(f'incluir_{tipo}') == 'on')) for tipo, label in TIPOS]
    error = ''
    activa = 'computador'
    if data is not None:
        validos = [fs.is_valid() for _, _, fs, incluido in secciones if incluido]
        destino_valido = destino.is_valid()
        if not validos:
            error = 'Debe incluir al menos un computador, monitor o producto.'
        elif all(validos) and destino_valido:
            try:
                entrega = guardar(request, destino, secciones)
                return redirect('inventario_tic:estacion_detalle', pk=entrega.pk)
            except ValidationError as exc:
                error = ' '.join(exc.messages)
            except IntegrityError:
                error = 'No se pudo confirmar: un registro fue creado o modificado simultáneamente. Revise las series e intente nuevamente.'
        activa = next((tipo for tipo, _, fs, incluido in secciones if incluido and (fs.errors and any(fs.errors) or fs.non_form_errors())), 'destino' if not destino_valido else 'computador')
    return render(request, 'inventario_tic/estaciones/form.html', {
        'title': 'Asignar estación de trabajo', 'destino': destino, 'secciones': secciones,
        'error': error, 'activa': activa, 'funcionario_form': FormFuncionarioInventario(),
        'modelos': list(visibles(Modelo, request.user).values('id', 'nombre', 'marca_id')),
    })


@login_required
@require_GET
def buscar(request):
    exigir_establecimiento(request.user)
    tipo = request.GET.get('tipo')
    model = {'computador': Computador, 'monitores': Monitor, 'productos': Producto}.get(tipo)
    if model is None:
        return JsonResponse({'results': []}, status=400)
    qs = visibles(model, request.user)
    term = request.GET.get('q', '').strip()[:150]
    if tipo == 'productos':
        qs = qs.filter(stock_disponible__gt=0).filter(Q(nombre__icontains=term) | Q(tipo_producto__nombre__icontains=term))
    else:
        qs = qs.filter(asignado=False, responsable__isnull=True).filter(Q(codigo_inventario__icontains=term) | Q(numero_serie__icontains=term))
        qs = qs.select_related('marca', 'modelo')
    return JsonResponse({'results': [{'value': str(o.pk), 'text': f'{o} — stock: {o.stock_disponible}' if tipo == 'productos' else f'{o} — serie: {o.numero_serie}'} for o in qs.order_by('pk')[:30]]})


def entrega_visible(request, pk):
    qs = AsignacionEstacion.objects.all()
    if not request.user.is_superuser:
        qs = qs.filter(establecimiento_id=request.user.establecimiento_id) if request.user.establecimiento_id else qs.none()
    return get_object_or_404(qs, pk=pk)


@login_required
def listado(request):
    qs = AsignacionEstacion.objects.select_related('responsable', 'destino')
    if not request.user.is_superuser:
        qs = qs.filter(establecimiento_id=request.user.establecimiento_id) if request.user.establecimiento_id else qs.none()
    if request.method == 'POST':
        if request.POST.get('action') != 'search':
            return JsonResponse({'error': 'Acción no válida.'}, status=400)

        def entero(nombre, default):
            try:
                return int(request.POST.get(nombre, default))
            except (TypeError, ValueError):
                return default

        total = qs.count()
        search = request.POST.get('search[value]', '').strip()
        if search:
            filtros = Q(contenido__destino__icontains=search) | Q(contenido__responsable__icontains=search)
            if search.isdecimal() and len(search) <= 18:
                filtros |= Q(pk=int(search))
            qs = qs.filter(filtros)
        filtrados = qs.count()
        columnas = {0: 'pk', 1: 'created_at', 2: 'contenido__destino', 3: 'contenido__responsable'}
        campo = columnas.get(entero('order[0][column]', 0), 'pk')
        if request.POST.get('order[0][dir]', 'desc') != 'asc':
            campo = f'-{campo}'
        qs = qs.order_by(campo, '-pk')
        start = max(0, entero('start', 0))
        length = entero('length', 10)
        if length != -1:
            qs = qs[start:start + (length if length > 0 else 10)]
        data = []
        for entrega in qs:
            fecha = entrega.created_at
            if timezone.is_aware(fecha):
                fecha = timezone.localtime(fecha)
            data.append({
                'id': entrega.pk, 'fecha': fecha.strftime('%d/%m/%Y %H:%M'),
                'establecimiento': entrega.contenido.get('destino', ''),
                'responsable': entrega.contenido.get('responsable', ''),
                'detalle_url': reverse('inventario_tic:estacion_detalle', args=[entrega.pk]),
                'acta_url': reverse('inventario_tic:estacion_acta', args=[entrega.pk]),
            })
        return JsonResponse({'draw': max(0, entero('draw', 1)), 'recordsTotal': total,
                             'recordsFiltered': filtrados, 'data': data})
    return render(request, 'inventario_tic/estaciones/listado.html', {'title': 'Estaciones de trabajo'})


@login_required
def detalle(request, pk):
    return render(request, 'inventario_tic/estaciones/detalle.html', {'title': 'Entrega de estación de trabajo', 'entrega': entrega_visible(request, pk)})


@login_required
def acta(request, pk):
    from weasyprint import HTML
    entrega = entrega_visible(request, pk)
    fecha_emision = timezone.now()
    if timezone.is_aware(fecha_emision):
        fecha_emision = timezone.localtime(fecha_emision)
    contexto = {'entrega': entrega, 'fecha_emision': fecha_emision}
    logo_path = finders.find('core/media/logo_ssa.png')
    if logo_path:
        contexto['logo_servicio'] = 'data:image/png;base64,' + base64.b64encode(Path(logo_path).read_bytes()).decode('ascii')
    html = render_to_string('inventario_tic/estaciones/acta.html', contexto, request=request)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="acta_estacion_{entrega.pk}.pdf"'
    HTML(string=html, base_url=request.build_absolute_uri()).write_pdf(response)
    return response
