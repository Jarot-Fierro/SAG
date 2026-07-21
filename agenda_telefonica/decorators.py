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

        perfil = getattr(request.user, 'perfilagenda', None)
        if not perfil:
            messages.error(request, "Su usuario no tiene un perfil de agenda configurado. Contacte al administrador.")
            return redirect('intranet:index')

        if perfil.editor:
            return view_func(request, *args, **kwargs)

        messages.error(request, "No tiene permisos para acceder a esta sección.")
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect('intranet:index')

    return _wrapped_view


def user_mantenedores_module(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debe iniciar sesión para acceder a este módulo.")
            return redirect(f'/usuarios/login/?next={request.path}')

        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        perfil = getattr(request.user, 'perfilagenda', None)
        if not perfil:
            messages.error(request, "Su usuario no tiene un perfil de agenda configurado. Contacte al administrador.")
            return redirect('intranet:index')

        if perfil.editor and perfil.mantenedores:
            return view_func(request, *args, **kwargs)

        messages.error(request, "No tiene permisos para acceder a la sección de mantenedores.")
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect('intranet:index')

    return _wrapped_view
