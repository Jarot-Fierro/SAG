"""Operaciones atómicas de entrega; el bloqueo de activos coordina ambos flujos."""
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.utils import timezone
from gestion_tic.models import (EntregaActivos, Activo, MovimientoActivo,
                                MovimientoActivoAccesorio, Accesorio, Ips)


def validar_disponibilidad(activo, bloquear=False):
    if not activo.is_active or activo.de_baja:
        raise ValidationError('El activo está inactivo o dado de baja.')
    movimientos = activo.movimientos.all()
    if bloquear:
        movimientos = movimientos.select_for_update()
    ultimo = movimientos.order_by('-created_at', '-id').first()
    if ultimo and ultimo.entrega_id and ultimo.entrega.estado == EntregaActivos.Estado.PENDIENTE:
        raise ValidationError('El activo pertenece a una entrega pendiente de recepción.')
    return ultimo


@transaction.atomic
def confirmar_entrega(entrega_id, user):
    entrega = EntregaActivos.objects.select_for_update().get(pk=entrega_id)
    if (not user.has_perm('gestion_tic.add_movimientoactivo')
            or user.establecimiento_id != entrega.establecimiento_id):
        raise PermissionDenied('No tiene permiso para confirmar esta entrega.')
    if entrega.estado != EntregaActivos.Estado.BORRADOR:
        raise ValidationError('La entrega ya fue confirmada.')
    if not entrega.funcionario.is_active or entrega.funcionario.establecimiento_id != entrega.establecimiento_id:
        raise ValidationError('El destinatario no está disponible en este establecimiento.')
    if not entrega.tipo_movimiento.is_active or not entrega.tipo_movimiento.requiere_recepcion:
        raise ValidationError('Seleccione un tipo de movimiento que requiera recepción.')
    if (entrega.tipo_movimiento.establecimiento_id != entrega.establecimiento_id
            or entrega.jefe_firmante.establecimiento_id != entrega.establecimiento_id
            or not entrega.jefe_firmante.is_active):
        raise ValidationError('El tipo de movimiento o firmante no está disponible.')
    detalles = list(entrega.detalles.select_related('activo').order_by('activo_id'))
    if not detalles:
        raise ValidationError('Agregue al menos un activo al carrito.')
    activos = {a.pk: a for a in Activo.objects.select_for_update().filter(
        pk__in=[d.activo_id for d in detalles]).order_by('pk')}
    # Bloquear todas las IP en orden antes de cambiar su disponibilidad.
    anteriores = {}
    for detalle in detalles:
        activo = activos[detalle.activo_id]
        if activo.establecimiento_id != entrega.establecimiento_id:
            raise ValidationError('El activo pertenece a otro establecimiento.')
        anteriores[activo.pk] = validar_disponibilidad(activo, bloquear=True)
    ip_ids = {d.ip_id for d in detalles if d.ip_id}
    ip_ids.update(m.ip_id for m in anteriores.values() if m and m.ip_id)
    ips = {ip.pk: ip for ip in Ips.objects.select_for_update().filter(pk__in=ip_ids).order_by('pk')}
    usadas = set()
    for detalle in detalles:
        anterior = anteriores[detalle.activo_id]
        old_ip_id = anterior.ip_id if anterior else None
        if detalle.ip_id:
            ip = ips[detalle.ip_id]
            if (detalle.ip_id in usadas or not ip.is_active
                    or ip.establecimiento_id != entrega.establecimiento_id
                    or (ip.asignado and ip.pk != old_ip_id)):
                raise ValidationError('Una IP seleccionada ya está ocupada o no está disponible.')
            if not activos[detalle.activo_id].utiliza_ip:
                raise ValidationError('Este activo no utiliza IP.')
            usadas.add(ip.pk)
        # Cada movimiento conserva sus accesorios, IP y datos de destinatario.
        movimiento = MovimientoActivo.objects.create(
            entrega=entrega, activo=activos[detalle.activo_id],
            establecimiento=entrega.establecimiento, funcionario=entrega.funcionario,
            unidad_organizacional=entrega.funcionario.unidad_organizacional,
            nombre_completo=str(entrega.funcionario),
            departamento=(entrega.funcionario.unidad_organizacional.nombre
                          if entrega.funcionario.unidad_organizacional else ''),
            tipo_movimiento=entrega.tipo_movimiento, jefe_firmante=entrega.jefe_firmante,
            ip_id=detalle.ip_id, observacion=detalle.observacion,
            created_by=user, updated_by=user)
        for item in detalle.accesorios:
            accesorio = Accesorio.objects.filter(pk=item['id'], is_active=True,
                                                establecimiento=entrega.establecimiento).first()
            if not accesorio:
                raise ValidationError('Uno de los accesorios ya no está disponible.')
            MovimientoActivoAccesorio.objects.create(
                movimiento=movimiento, accesorio=accesorio, nombre=accesorio.nombre,
                cantidad=item['cantidad'], observacion=item.get('observacion', ''),
                establecimiento=entrega.establecimiento, created_by=user, updated_by=user)
    for ip in ips.values():
        ip.asignado = ip.pk in usadas
        ip.save()
    entrega.estado = EntregaActivos.Estado.PENDIENTE
    entrega.updated_by = user
    # Se congela lo entregado antes de que el catálogo pueda cambiar.
    entrega.snapshot_acta = {
        'folio': entrega.pk, 'observacion': entrega.observacion,
        'establecimiento': entrega.establecimiento.nombre,
        'nombre_completo': str(entrega.funcionario),
        'departamento': (entrega.funcionario.unidad_organizacional.nombre
                         if entrega.funcionario.unidad_organizacional else ''),
        'activos': [m.generar_snapshot_acta() for m in entrega.movimientos.order_by('pk')],
    }
    entrega.save()
    return entrega


def puede_recepcionar_entrega(entrega, user):
    return (
        user.establecimiento_id == entrega.establecimiento_id
        and (user.funcionario_id == entrega.funcionario_id
             or user.has_perm('gestion_tic.add_movimientoactivo'))
    )


@transaction.atomic
def recepcionar_entrega(entrega_id, user):
    entrega = EntregaActivos.objects.select_for_update().get(pk=entrega_id)
    if not puede_recepcionar_entrega(entrega, user):
        raise PermissionDenied('Se requiere ser el destinatario o tener permiso para registrar movimientos en este establecimiento.')
    if entrega.estado != EntregaActivos.Estado.PENDIENTE:
        raise ValidationError('La entrega no está pendiente de recepción.')
    movimientos = list(entrega.movimientos.order_by('pk'))
    activos = list(Activo.objects.select_for_update().filter(
        pk__in=[m.activo_id for m in movimientos]).order_by('pk'))
    if not movimientos or len(activos) != len(movimientos):
        raise ValidationError('La entrega no contiene movimientos válidos.')
    fecha = timezone.now()
    snapshots = entrega.snapshot_acta['activos']
    if len(snapshots) != len(movimientos):
        raise ValidationError('El detalle histórico de la entrega está incompleto.')
    for mov, snapshot in zip(movimientos, snapshots):
        ultimo = mov.activo.movimientos.select_for_update().order_by('-created_at', '-id').first()
        if ultimo.pk != mov.pk or mov.recepcionado:
            raise ValidationError('Existe un movimiento posterior o un activo ya recepcionado.')
        mov.recepcionado = True
        mov.fecha_recepcion = fecha
        mov.recepcionado_por = user
        mov.updated_by = user
        mov.snapshot_acta = dict(snapshot, fecha_recepcion=fecha.strftime('%d/%m/%Y %H:%M'))
        mov.save()
    entrega.estado = EntregaActivos.Estado.RECEPCIONADA
    entrega.fecha_recepcion = fecha
    entrega.recepcionado_por = user
    entrega.updated_by = user
    entrega.snapshot_acta = dict(entrega.snapshot_acta,
        activos=[m.snapshot_acta for m in movimientos],
        fecha_recepcion=fecha.strftime('%d/%m/%Y %H:%M'),
        recepcionado_por=user.get_username())
    entrega.save()
    return entrega
