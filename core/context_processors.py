from django.urls import resolve

from core.models.establecimientos import Establecimiento
from core.models.modulos import Modulo


def modulo_actual_processor(request):
    try:
        # Obtenemos el namespace de la URL actual (que coincide con el 'codigo' en tu modelo)
        match = resolve(request.path_info)
        app_name = match.app_name
        modulo = Modulo.objects.filter(codigo=app_name, is_active=True).first()
        return {'modulo_actual': modulo}
    except:
        return {'modulo_actual': None}


def establecimientos_processor(request):
    if request.user.is_authenticated:
        return {
            'global_establecimientos': Establecimiento.objects.filter(is_active=True).order_by('nombre')
        }
    return {}
