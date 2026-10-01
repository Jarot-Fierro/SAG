from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


def user_is_vpn_gestor(user):
    """
    Determina si un usuario tiene permisos de gestión para la Bandeja TIC de solicitudes VPN.
    Verifica superusuario, permiso específico o PerfilVPN.bandeja_vpn.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if user.has_perm('solicitud_vpn.can_manage_vpn'):
        return True
    if hasattr(user, 'perfil_vpn') and user.perfil_vpn and getattr(user.perfil_vpn, 'is_active', True):
        return bool(getattr(user.perfil_vpn, 'bandeja_vpn', False))
    return False


class VPNRequiredMixin(LoginRequiredMixin):
    """
    Mixin para vistas que requieren rol de gestión TIC / Informática de solicitudes VPN.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not user_is_vpn_gestor(request.user):
            messages.error(request, "No tiene permisos para acceder a la Bandeja de Gestión VPN.")
            return redirect('solicitud_vpn:mis_solicitudes')
        return super().dispatch(request, *args, **kwargs)


def vpn_required(view_func):
    """
    Decorador para funciones/vistas que requieren rol de gestión TIC de solicitudes VPN.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debe iniciar sesión para realizar esta acción.")
            return redirect(f'/usuarios/login/?next={request.path}')
        if not user_is_vpn_gestor(request.user):
            messages.error(request, "No tiene permisos de gestión VPN para realizar esta acción.")
            return redirect('solicitud_vpn:mis_solicitudes')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
