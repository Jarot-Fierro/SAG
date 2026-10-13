from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied

from solicitud_codigo.models import PerfilCodigo


def get_perfil_codigo(user):
    if not user or not user.is_authenticated:
        return None
    try:
        return user.perfil_codigo
    except (PerfilCodigo.DoesNotExist, AttributeError):
        return None


def user_can_solicitar(user):
    if not user or not user.is_authenticated:
        return False
    if not hasattr(user, 'establecimiento') or not user.establecimiento:
        return False
    perfil = get_perfil_codigo(user)
    if perfil is not None:
        return perfil.puede_solicitar and perfil.is_active
    return True


def user_is_referente(user):
    if not user or not user.is_authenticated:
        return False
    perfil = get_perfil_codigo(user)
    if not perfil or not perfil.is_active:
        return False
    return perfil.es_referente


def user_can_validate(user):
    if not user or not user.is_authenticated:
        return False
    perfil = get_perfil_codigo(user)
    if not perfil or not perfil.is_active:
        return False
    return perfil.es_referente and perfil.puede_validar


def user_can_create_codes(user):
    if not user or not user.is_authenticated:
        return False
    perfil = get_perfil_codigo(user)
    if not perfil or not perfil.is_active:
        return False
    return perfil.puede_crear_codigos


def user_can_manage_solicitud(user, solicitud):
    if not user or not user.is_authenticated or not solicitud:
        return False
    perfil = get_perfil_codigo(user)
    if not perfil or not perfil.is_active or not perfil.es_referente:
        return False
    return perfil.puede_gestionar_solicitud(solicitud)


class SolicitanteRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return user_can_solicitar(self.request.user)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied("No tiene autorización para ingresar solicitudes de códigos o no tiene establecimiento asignado.")


class ReferenteRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return user_is_referente(self.request.user)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied("No cuenta con perfil de Referente autorizado para la gestión de solicitudes de códigos.")


class CreadorCodigoRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return user_can_create_codes(self.request.user)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied("No cuenta con autorización expresa para registrar la creación efectiva de códigos SISSA.")
