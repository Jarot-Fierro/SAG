from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django_user_agents.utils import get_user_agent

from core.models.usuarios import HistorialAcceso


def get_client_ip(request):
    """
    Obtiene la dirección IP del cliente, considerando si está detrás de un proxy.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Tomar únicamente la primera IP de HTTP_X_FORWARDED_FOR
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@receiver(user_logged_in)
def register_login_access(sender, request, user, **kwargs):
    """
    Registra un nuevo acceso en el historial cuando el inicio de sesión es exitoso.
    """
    if request:
        user_agent = get_user_agent(request)

        # Determinar el tipo de dispositivo (equipo)
        if user_agent.is_mobile:
            device = 'Mobile'
        elif user_agent.is_tablet:
            device = 'Tablet'
        elif user_agent.is_pc:
            device = 'PC'
        elif user_agent.is_bot:
            device = 'Bot'
        else:
            device = 'Unknown'

        # Crear el registro en el historial
        HistorialAcceso.objects.create(
            usuario=user,
            establecimiento=getattr(user, 'establecimiento', None),
            ip=get_client_ip(request),
            equipo=device,
            navegador=user_agent.browser.family,
            version_navegador=user_agent.browser.version_string,
            sistema_operativo=user_agent.os.family
        )
