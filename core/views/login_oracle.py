import json
import logging
from time import perf_counter

import oracledb
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST, require_http_methods

from .oracle import recordset

logger = logging.getLogger(__name__)


@sensitive_post_parameters('password')
@never_cache
@require_http_methods(['GET', 'POST'])
def index(request):
    logger.debug('Inicio de login: metodo=%s, sesion_oracle_activa=%s',
                 request.method, bool(request.session.get('oracle_user')))
    error = ''
    username = ''
    areas = []
    profile = None
    login_success = False
    # Limpiar la contraseña que guardaba la versión anterior.
    request.session.pop('oracle_password', None)
    if 'Password' in request.session.get('oracle_profile', {}):
        previous_profile = dict(request.session['oracle_profile'])
        previous_profile.pop('Password', None)
        request.session['oracle_profile'] = previous_profile
    selected_area = request.POST.get('area', '')
    action = request.POST.get('action', 'areas')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        logger.debug('Formulario recibido: usuario_presente=%s, password_presente=%s',
                     bool(username), bool(password))
        if not username or not password:
            logger.debug('Validacion detenida: faltan credenciales.')
            error = 'Ingresa usuario y contraseña.'
        elif not settings.ORACLE_SERVICE_NAME and not settings.ORACLE_SID:
            logger.error('Configuracion incompleta: falta SERVICE_NAME o SID.')
            error = 'Falta configurar el SERVICE_NAME o SID de Oracle en el servidor.'
        else:
            started = perf_counter()
            try:
                target = ({'service_name': settings.ORACLE_SERVICE_NAME}
                          if settings.ORACLE_SERVICE_NAME
                          else {'sid': settings.ORACLE_SID})
                logger.debug('Abriendo conexion Oracle: host=%s, puerto=%s, destino=%s, modo=%s',
                             settings.ORACLE_HOST, settings.ORACLE_PORT, target,
                             'Thin' if oracledb.is_thin_mode() else 'Thick')
                # Oracle valida al usuario al abrir su propia sesión.
                with oracledb.connect(
                        user=username,
                        password=password,
                        host=settings.ORACLE_HOST,
                        port=settings.ORACLE_PORT,
                        tcp_connect_timeout=5,
                        **target,
                ) as connection:
                    connection.call_timeout = 15000
                    logger.info('Oracle acepto las credenciales; conexion abierta.')
                    areas = recordset(connection, 'areas', [username.upper()])
                    if not areas:
                        error = 'El usuario no tiene áreas habilitadas en el sistema.'
                    elif action == 'login':
                        allowed = {str(row['codigo_area']) for row in areas}
                        if selected_area not in allowed:
                            error = 'Selecciona un área habilitada para tu usuario.'
                        else:
                            records = recordset(connection, 'perfil',
                                                [username.upper(), int(selected_area), None, None])
                            if records:
                                profile = records[0]
                            else:
                                error = 'El usuario no tiene un perfil habilitado para esta área.'
                logger.debug('Conexion Oracle cerrada; duracion=%.3fs.', perf_counter() - started)
            except oracledb.Error as exc:
                code = getattr(exc.args[0], 'code', None) if exc.args else None
                # Solo codigos: no volcar credenciales, POST ni objetos de sesion.
                logger.warning('Error Oracle: tipo=%s, codigo=%s, codigo_completo=%s, duracion=%.3fs',
                               type(exc).__name__, code,
                               getattr(exc.args[0], 'full_code', 'desconocido') if exc.args else 'desconocido',
                               perf_counter() - started)
                if code in (1017, 28000, 28001):
                    logger.debug('Acceso rechazado por Oracle; no se crea sesion Django.')
                    error = 'Oracle rechazó el acceso: credenciales incorrectas, cuenta bloqueada o contraseña vencida.'
                else:
                    logger.warning('No se pudo conectar a Oracle (%s).',
                                   getattr(exc.args[0], 'full_code', 'desconocido') if exc.args else 'desconocido')
                    error = 'No se pudo conectar a Oracle o consultar las funciones de seguridad. Revisa el código de error en consola.'
            else:
                if profile is not None:
                    logger.debug('Perfil validado; eliminando sesion anterior de Django.')
                    request.session.flush()
                    request.session['oracle_user'] = username
                    fields = {
                        'CodCentroOrg': 'codigo_organico', 'CentroOrganico': 'nombre',
                        'Rut': 'rut_usuario', 'Nombre': 'nombre_usuario',
                        'CodPerfil': 'codigo_perfil', 'Perfil': 'descripcion_perfil',
                        'Area': 'codigo_area', 'NombreArea': 'descripcion_area',
                        'User': 'usuario',
                    }
                    request.session['oracle_profile'] = {
                        key: str(profile[column]) if profile.get(column) is not None else None
                        for key, column in fields.items()
                    }
                    request.session.save()
                    login_success = True
                    logger.info('Perfil validado y sesion Django guardada; mostrando resultado del login.')
                else:
                    logger.debug('Sin sesion autenticada: esperando seleccion de area o perfil valido.')
    session_data = dict(request.session.items())
    if login_success:
        # Copia solo para la respuesta HTML, nunca se asigna a request.session.
        session_data['oracle_profile'] = dict(session_data['oracle_profile'], Password=password)
    logger.debug('Renderizando index.html: error=%s, sesion_oracle_activa=%s',
                 bool(error), bool(request.session.get('oracle_user')))
    return render(request, 'index.html', {
        'error': error, 'username': username, 'areas': areas,
        'selected_area': selected_area,
        'session_json': json.dumps(session_data,
                                   cls=DjangoJSONEncoder, ensure_ascii=False, indent=4)
        if request.session.get('oracle_user') else '',
    })


@require_POST
def logout(request):
    logger.debug('Cierre de sesion solicitado: sesion_oracle_activa=%s',
                 bool(request.session.get('oracle_user')))
    request.session.flush()
    logger.info('Sesion Django eliminada; redirigiendo al index.')
    return redirect('index')
