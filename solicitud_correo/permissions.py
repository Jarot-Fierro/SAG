from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


def user_is_rrhh(user):
    """
    Determina si un usuario tiene permisos de Recursos Humanos.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if user.has_perm('solicitud_correo.can_review_rrhh'):
        return True
    if user.groups.filter(name__iregex=r'rr\.?hh\.?|recursos humanos|personal|gestion de personas|gestión de personas').exists():
        return True
    if hasattr(user, 'funcionario') and user.funcionario and user.funcionario.unidad_organizacional:
        nombre_uo = user.funcionario.unidad_organizacional.nombre.upper()
        if any(k in nombre_uo for k in ['RECURSOS HUMANOS', 'RRHH', 'RR.HH', 'PERSONAL', 'PERSONAS']):
            return True
    return False


def user_is_tic(user):
    """
    Determina si un usuario tiene permisos de TIC / Informática.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if user.has_perm('solicitud_correo.can_process_tic'):
        return True
    if hasattr(user, 'perfil_soporte') and user.perfil_soporte and getattr(user.perfil_soporte, 'is_active', True):
        return True
    if user.groups.filter(name__iregex=r'tic|informatica|informática|soporte|sistemas|tecnolog').exists():
        return True
    if hasattr(user, 'funcionario') and user.funcionario and user.funcionario.unidad_organizacional:
        nombre_uo = user.funcionario.unidad_organizacional.nombre.upper()
        if any(k in nombre_uo for k in ['INFORMATICA', 'INFORMÁTICA', 'TIC', 'TECNOLOG', 'SISTEMAS']):
            return True
    return False


def user_can_notify(user):
    """
    Determina si el usuario puede registrar o enviar notificaciones a funcionarios.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user_is_rrhh(user) or user_is_tic(user):
        return True
    return user.has_perm('solicitud_correo.can_notify_funcionario')


class RRHHRequiredMixin(LoginRequiredMixin):
    """
    Mixin para vistas que requieren rol de RR.HH.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not user_is_rrhh(request.user):
            messages.error(request, "No tiene permisos de Recursos Humanos para acceder a esta sección.")
            return redirect('solicitud_correo:mis_solicitudes')
        return super().dispatch(request, *args, **kwargs)


class TICRequiredMixin(LoginRequiredMixin):
    """
    Mixin para vistas que requieren rol de TIC / Informática.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not user_is_tic(request.user):
            messages.error(request, "No tiene permisos de TIC / Informática para acceder a esta sección.")
            return redirect('solicitud_correo:mis_solicitudes')
        return super().dispatch(request, *args, **kwargs)


def rrhh_required(view_func):
    """
    Decorador para funciones que requieren rol de RR.HH.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debe iniciar sesión para realizar esta acción.")
            return redirect(f'/usuarios/login/?next={request.path}')
        if not user_is_rrhh(request.user):
            messages.error(request, "No tiene permisos de Recursos Humanos para realizar esta acción.")
            return redirect('solicitud_correo:mis_solicitudes')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def tic_required(view_func):
    """
    Decorador para funciones que requieren rol de TIC.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debe iniciar sesión para realizar esta acción.")
            return redirect(f'/usuarios/login/?next={request.path}')
        if not user_is_tic(request.user):
            messages.error(request, "No tiene permisos de TIC para realizar esta acción.")
            return redirect('solicitud_correo:mis_solicitudes')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
