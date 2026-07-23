import hashlib
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from core.models.recuperacion_password import RecuperacionPassword
from core.services.email_service import EmailService

User = get_user_model()
logger = logging.getLogger(__name__)


class PasswordRecoveryService:
    @staticmethod
    def _generate_token():
        return secrets.token_urlsafe(32)

    @staticmethod
    def _hash_token(token):
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def create_recovery_request(rut, request):
        """
        Crea una solicitud de recuperación de contraseña.
        """
        # Rate limiting por IP
        ip = PasswordRecoveryService.get_client_ip(request)
        recent_ip_requests = RecuperacionPassword.objects.filter(
            ip_solicitud=ip,
            fecha_creacion__gte=timezone.now() - timedelta(minutes=settings.PASSWORD_RECOVERY_RATE_LIMIT_MINUTES)
        ).count()

        if recent_ip_requests >= settings.PASSWORD_RECOVERY_MAX_REQUESTS_PER_IP:
            logger.warning(f"Rate limit alcanzado para IP: {ip}")
            return True  # Retornar True para no dar pistas al usuario

        user = User.objects.filter(username=rut.upper(), is_active=True).first()

        if not user:
            logger.warning(f"Intento de recuperación para RUT inexistente o inactivo: {rut}")
            # Registrar intento fallido si se desea (podría ser un modelo aparte o este mismo sin usuario)
            return True

        # Rate limiting por usuario
        recent_user_requests = RecuperacionPassword.objects.filter(
            usuario=user,
            fecha_creacion__gte=timezone.now() - timedelta(minutes=settings.PASSWORD_RECOVERY_RATE_LIMIT_MINUTES)
        ).count()

        if recent_user_requests >= settings.PASSWORD_RECOVERY_MAX_REQUESTS_PER_USER:
            logger.warning(f"Rate limit alcanzado para usuario: {user.username}")
            return True

        token = PasswordRecoveryService._generate_token()
        token_hash = PasswordRecoveryService._hash_token(token)

        # Expiración
        expiration = timezone.now() + timedelta(minutes=settings.PASSWORD_RECOVERY_EXPIRATION_MINUTES)

        # Obtener info del dispositivo
        user_agent = request.user_agent

        recovery = RecuperacionPassword.objects.create(
            usuario=user,
            establecimiento=user.establecimiento,
            token_hash=token_hash,
            fecha_expiracion=expiration,
            ip_solicitud=ip,
            user_agent_solicitud=str(user_agent),
            navegador_solicitud=user_agent.browser.family,
            version_navegador_solicitud=user_agent.browser.version_string,
            sistema_operativo_solicitud=user_agent.os.family,
            dispositivo_solicitud=user_agent.device.family,
            es_pc_solicitud=user_agent.is_pc,
            es_tablet_solicitud=user_agent.is_tablet,
            es_movil_solicitud=user_agent.is_mobile,
            es_bot_solicitud=user_agent.is_bot,
        )

        base_url = settings.PASSWORD_RECOVERY_BASE_URL.rstrip('/')
        if '://' not in base_url:
            if base_url.startswith('http:'):
                base_url = base_url.replace('http:', 'http://', 1)
            elif base_url.startswith('https:'):
                base_url = base_url.replace('https:', 'https://', 1)
            else:
                base_url = f"http://{base_url}"

        token_url = f"{base_url}{reverse('recuperacion_password:reset_password', kwargs={'token': token})}"

        # Enviar correo
        success = EmailService.send_recovery_email(user, recovery, token_url)

        if not success:
            recovery.solicitud_exitosa = False
            recovery.observacion = "Error al enviar el correo o configuración SMTP no encontrada."
            recovery.save()
            logger.error(f"Error al enviar correo de recuperación para {user.username}")
        else:
            logger.info(f"Solicitud de recuperación creada y enviada para {user.username}")

        return True

    @staticmethod
    def validate_token(token):
        """
        Valida si un token es válido, no ha expirado y no ha sido utilizado.
        """
        token_hash = PasswordRecoveryService._hash_token(token)
        recovery = RecuperacionPassword.objects.filter(token_hash=token_hash).first()

        if not recovery:
            logger.warning(f"Token no encontrado: {token_hash}")
            return None, "El enlace de recuperación ya no es válido o ha expirado."

        if recovery.utilizado or recovery.estado != 'PENDIENTE':
            logger.warning(f"Token ya utilizado o en estado no pendiente: {token_hash}")
            return None, "El enlace de recuperación ya ha sido utilizado."

        if recovery.is_expired():
            recovery.estado = 'EXPIRADO'
            recovery.save()
            logger.warning(f"Token expirado: {token_hash}")
            return None, "El enlace de recuperación ha expirado."

        return recovery, None

    @staticmethod
    def reset_password(recovery, new_password, request):
        """
        Realiza el cambio de contraseña y actualiza la auditoría.
        """
        user = recovery.usuario
        user.set_password(new_password)
        user.save()

        # Actualizar recuperación
        user_agent = request.user_agent
        recovery.utilizado = True
        recovery.fecha_utilizacion = timezone.now()
        recovery.estado = 'UTILIZADO'
        recovery.ip_utilizacion = PasswordRecoveryService.get_client_ip(request)
        recovery.user_agent_utilizacion = str(user_agent)
        recovery.navegador_utilizacion = user_agent.browser.family
        recovery.version_navegador_utilizacion = user_agent.browser.version_string
        recovery.sistema_operativo_utilizacion = user_agent.os.family
        recovery.dispositivo_utilizacion = user_agent.device.family
        recovery.es_pc_utilizacion = user_agent.is_pc
        recovery.es_tablet_utilizacion = user_agent.is_tablet
        recovery.es_movil_utilizacion = user_agent.is_mobile
        recovery.es_bot_utilizacion = user_agent.is_bot
        recovery.save()

        logger.info(f"Contraseña cambiada exitosamente para el usuario {user.username}")

        # Opción para invalidar otras sesiones (futuro)
        # update_session_auth_hash(request, user) # Si estuviéramos logueados, pero aquí no lo estamos necesariamente

        return True

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
