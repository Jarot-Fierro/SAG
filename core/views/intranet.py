from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def intranet(request):
    modulos = request.user.modulos.filter(is_active=True)
    return render(request, 'intranet/index.html', {'modulos': modulos})


from django.utils.dateparse import parse_datetime


def mantenimiento_view(request):
    """
    Vista genérica para mostrar el estado de mantenimiento de un módulo.
    Espera 'mantenimiento_hasta' en el contexto, pasado usualmente por el middleware.
    """
    mantenimiento_hasta_str = request.session.get('mantenimiento_hasta')
    mantenimiento_hasta = None
    if mantenimiento_hasta_str:
        mantenimiento_hasta = parse_datetime(mantenimiento_hasta_str)

    return render(request, 'mantenimiento.html', {
        'mantenimiento_hasta': mantenimiento_hasta
    })
