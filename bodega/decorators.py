from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def perfil_bodega_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        try:
            request.perfil_bodega = request.user.perfil_bodega
        except Exception:
            messages.error(request, "No posee un perfil de bodega asignado.")
            return redirect("intranet:index")

        return view_func(request, *args, **kwargs)

    return _wrapped_view
