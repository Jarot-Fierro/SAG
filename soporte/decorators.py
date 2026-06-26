from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import PerfilSoporte


def soporte_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1. Verificar si el usuario está logueado
        if not request.user.is_authenticated:
            return redirect('usuarios:login')  # O la URL de login que use el proyecto

        # 2. Buscar al usuario en PerfilSoporte y verificar usuario_soporte=True
        # Nota: usuario es un ManyToManyField en PerfilSoporte
        perfil = PerfilSoporte.objects.filter(usuario=request.user, usuario_soporte=True).exists()

        if perfil:
            return view_func(request, *args, **kwargs)

        # Si no tiene permiso, redirigir o mostrar error. 
        # Usualmente en estos casos se redirige al index con un mensaje.
        messages.error(request, "No tienes permisos de soporte para acceder a esta vista.")
        return redirect('intranet:index')  # Redirigir a la página principal o donde corresponda

    return _wrapped_view
