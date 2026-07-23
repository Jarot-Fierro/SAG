# Módulo de Recuperación de Contraseña

Este módulo implementa un flujo seguro y desacoplado para la recuperación de contraseñas basado en el RUT del
funcionario.

## Arquitectura

El módulo sigue una arquitectura limpia dentro de la aplicación **core**, separando responsabilidades:

- **Models**: `ConfiguracionCorreo` (SMTP por establecimiento) y `RecuperacionPassword` (solicitudes y auditoría).
- **Services**: `EmailService` (envío de correos dinámico) y `PasswordRecoveryService` (lógica de negocio).
- **Forms**: Formularios validados para la solicitud y el cambio de contraseña.
- **Views**: Vistas que gestionan el flujo HTTP.
- **Templates**: Plantillas HTML para la web y para los correos electrónicos.

## Funcionamiento del EmailService

El `EmailService` permite el envío de correos utilizando configuraciones SMTP dinámicas almacenadas en la base de datos.

1. Se busca la `ConfiguracionCorreo` activa para el establecimiento del usuario.
2. Se crea una conexión SMTP en tiempo de ejecución utilizando los parámetros configurados.
3. Las contraseñas SMTP se almacenan cifradas en la base de datos mediante `cryptography.fernet`.
4. Si no hay configuración para un establecimiento, el sistema registra el evento en los logs pero no falla, manteniendo
   la seguridad (misma respuesta al usuario).

Cualquier otro módulo del ERP puede reutilizar `EmailService.send_email_with_config` pasando la configuración y el
contexto deseado.

## Flujo de Recuperación

1. **Solicitud**: El usuario ingresa su RUT. El sistema busca al usuario y su establecimiento.
2. **Generación de Token**: Se genera un token criptográficamente seguro con `secrets.token_urlsafe()`. Solo se almacena
   el hash SHA-256.
3. **Envío de Correo**: Se envía un enlace único al correo institucional registrado.
4. **Validación**: Al acceder al enlace, se valida la existencia del token, su expiración (30 min) y si ya fue
   utilizado.
5. **Cambio de Contraseña**: El usuario establece su nueva contraseña, la cual es validada por los validadores estándar
   de Django.

## Auditoría y Seguridad

- **django-user-agents**: Se registra automáticamente la información del dispositivo, navegador y sistema operativo
  tanto en la solicitud como en la utilización del token.
- **Rate Limiting**: Se limita el número de solicitudes por IP (5 cada 15 min) y por usuario (3 cada 15 min).
- **Protección contra enumeración**: El sistema siempre responde con el mismo mensaje genérico, exista o no el usuario.
- **Uso único**: Los tokens se marcan como utilizados y no pueden reutilizarse.
- **Cifrado**: Las contraseñas SMTP se cifran usando la `SECRET_KEY` del proyecto.

## Cómo extender el sistema

### Agregar Geolocalización

El modelo `RecuperacionPassword` ya cuenta con los campos `pais`, `region` y `ciudad`. Para activar la geolocalización:

1. Configurar `GeoIP2` en el proyecto.
2. Actualizar `PasswordRecoveryService.create_recovery_request` para llenar estos campos usando la IP del cliente.

### Reutilizar el envío de correos

Para enviar correos desde otros módulos:

```python
from core.services.email_service import EmailService
from core.models import ConfiguracionCorreo

config = ConfiguracionCorreo.objects.get(establecimiento=mi_establecimiento)
EmailService.send_email_with_config(
    config=config,
    subject="Asunto",
    recipient_list=["correo@ejemplo.com"],
    template_name="mi_app/email_template.html",
    context={'dato': 'valor'}
)
```
