from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import PerfilHoros


def perfil_horos_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            perfil = PerfilHoros.objects.get(usuario=request.user)
            if perfil.is_active:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "El usuario no tiene acceso a este modulo (Perfil inactivo).")
                return redirect('intranet:index')  # Asumiendo que existe una redirección segura
        except PerfilHoros.DoesNotExist:
            messages.error(request, "El usuario no tiene acceso a este modulo (Sin perfil).")
            return redirect('intranet:index')

    return _wrapped_view
