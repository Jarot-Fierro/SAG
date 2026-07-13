from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def user_editor_module(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debe iniciar sesión para acceder a este módulo.")
            return redirect(f'/usuarios/login/?next={request.path}')

        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        try:
            if request.user.perfilagenda.editor:
                return view_func(request, *args, **kwargs)
        except Exception:
            pass

        messages.error(request, "No tiene permisos para acceder a esta sección.")
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect('intranet:index')

    return _wrapped_view
