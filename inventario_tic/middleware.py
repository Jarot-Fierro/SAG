from django.conf import settings
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject

from .models import Celular, Computador, Impresora, Monitor
from .models.mantenedores import Contrato


CONTRATOS_AVISO_SESION = 'inventario_tic_contratos_aviso_mostrado'


def alertas_contratos(user):
    hoy = timezone.localdate() if settings.USE_TZ else timezone.now().date()
    contratos = Contrato.objects.filter(is_active=True, notificar_vencimiento=True,
                                        fecha_vencimiento__isnull=False)
    if not user.is_superuser:
        contratos = contratos.filter(establecimiento_id=user.establecimiento_id) if user.establecimiento_id else contratos.none()
    alertas = {}
    for contrato in contratos.order_by('fecha_vencimiento', 'nombre'):
        dias = (contrato.fecha_vencimiento - hoy).days
        if dias > contrato.dias_aviso:
            continue
        estado = f'Vencido hace {abs(dias)} días' if dias < 0 else 'Vence hoy' if dias == 0 else f'Vence en {dias} días'
        alertas[contrato.pk] = {'contrato': contrato, 'dias': dias, 'estado': estado,
                                'total': 0, 'equipos': [], 'cantidades': {}}
    if not alertas:
        return []
    for model, tipo, codigo in ((Celular, 'Celulares', 'imei'), (Impresora, 'Impresoras', 'numero_serie'),
                                (Monitor, 'Monitores', 'codigo_inventario'), (Computador, 'Computadores', 'codigo_inventario')):
        equipos = model.objects.filter(is_active=True, contrato_id__in=alertas)
        if not user.is_superuser:
            equipos = equipos.filter(establecimiento_id=user.establecimiento_id)
        campos = ['contrato_id', codigo]
        if model is not Celular and codigo != 'numero_serie':
            campos.append('numero_serie')
        for equipo in equipos.order_by('pk').values(*campos):
            alerta = alertas[equipo['contrato_id']]
            alerta['total'] += 1
            alerta['cantidades'][tipo] = alerta['cantidades'].get(tipo, 0) + 1
            alerta['equipos'].append({'tipo': tipo, 'codigo': equipo[codigo] or 'Sin código',
                                      'serie': equipo.get('numero_serie', '')})
    return [alerta for alerta in alertas.values() if alerta['total']]


class AlertasContratosMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        match = request.resolver_match
        if (match and match.app_name == 'inventario_tic' and request.user.is_authenticated
                and request.method == 'GET' and request.headers.get('X-Requested-With') != 'XMLHttpRequest'
                and request.headers.get('HX-Request') != 'true'
                and 'application/json' not in request.headers.get('Accept', '')):
            # La consulta solo se ejecuta si una página HTML renderiza el aviso.
            def cargar_alertas():
                alertas = alertas_contratos(request.user)
                request.abrir_alertas_contratos = not request.session.get(CONTRATOS_AVISO_SESION, False)
                if request.abrir_alertas_contratos:
                    request.session[CONTRATOS_AVISO_SESION] = True
                return alertas

            request.alertas_contratos = SimpleLazyObject(cargar_alertas)
