import logging

from django.core.mail import get_connection, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from core.models.configuracion_correo import ConfiguracionCorreo

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def send_email_with_config(config: ConfiguracionCorreo, subject, recipient_list, template_name, context):
        """
        Envía un correo electrónico utilizando una configuración SMTP específica.
        """
        try:
            # Crear conexión dinámica
            connection = get_connection(
                host=config.smtp_host,
                port=config.smtp_port,
                username=config.smtp_usuario,
                password=config.smtp_password,
                use_tls=config.smtp_tls,
                use_ssl=config.smtp_ssl,
            )

            html_content = render_to_string(template_name, context)

            # Versión de texto plano mejorada si es recuperación de contraseña
            if 'token_url' in context:
                text_content = (
                    f"Hola {context['usuario'].get_full_name() or context['usuario'].username},\n\n"
                    f"Hemos recibido una solicitud para restablecer la contraseña de su cuenta.\n\n"
                    f"Para proceder, copie y pegue el siguiente enlace en su navegador:\n\n"
                    f"{context['token_url']}\n\n"
                    f"Este enlace expirará en {context['expiration_minutes']} minutos.\n\n"
                    f"Si no solicitó este cambio, ignore este correo.\n\n"
                    f"SAG - Sistema de Administración y Gestión"
                )
            else:
                text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=f"{config.nombre_remitente} <{config.email_remitente}>",
                to=recipient_list,
                connection=connection,
            )
            email.attach_alternative(html_content, "text/html")

            result = email.send()
            if result:
                logger.info(
                    f"Correo enviado correctamente a {recipient_list} usando config de {config.establecimiento.nombre}")
            else:
                logger.warning(f"No se pudo enviar el correo a {recipient_list}")
            return result
        except Exception as e:
            logger.error(f"Error al enviar correo a {recipient_list}: {str(e)}")
            return False

    @staticmethod
    def send_recovery_email(usuario, recovery_request, token_url):
        """
        Centraliza el envío de correos de recuperación.
        """
        from django.conf import settings

        establecimiento = usuario.establecimiento
        if not establecimiento:
            logger.warning(f"Usuario {usuario.username} no tiene establecimiento asignado.")
            return False

        config = ConfiguracionCorreo.objects.filter(establecimiento=establecimiento, activo=True).first()
        if not config:
            logger.warning(f"No existe configuración SMTP activa para el establecimiento {establecimiento.nombre}")
            return False

        subject = settings.PASSWORD_RECOVERY_EMAIL_SUBJECT
        context = {
            'usuario': usuario,
            'token_url': token_url,
            'expiration_minutes': settings.PASSWORD_RECOVERY_EXPIRATION_MINUTES,
        }

        template_name = 'usuarios/emails/password_recovery.html'

        return EmailService.send_email_with_config(
            config=config,
            subject=subject,
            recipient_list=[usuario.email],
            template_name=template_name,
            context=context
        )
