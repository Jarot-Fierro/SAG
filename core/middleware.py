from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

from core.models.modulos import Modulo


class HtmxRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Si es una petición HTMX y hay una redirección (302)
        if request.headers.get('HX-Request') and response.status_code == 302:
            login_url = str(settings.LOGIN_URL)
            # Si la redirección es hacia la página de login
            if response['Location'].startswith(login_url):
                # Forzar a HTMX a redirigir la página completa
                response['HX-Redirect'] = response['Location']
        return response


class MantenimientoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Evitar bucles de redirección
        path = request.path
        mantenimiento_url = reverse('intranet:mantenimiento')

        if path == mantenimiento_url or path.startswith('/admin/') or path.startswith(
                '/usuarios/login/') or path.startswith('/usuarios/logout/'):
            return self.get_response(request)

        # Usar resolver para obtener el app_name (namespace)
        from django.urls import resolve
        try:
            match = resolve(path)
            app_name = match.app_name
        except:
            app_name = None

        if app_name:
            # Buscar el módulo por su código (que coincide con app_name)
            modulo = Modulo.objects.filter(codigo=app_name, en_mantenimiento=True, is_active=True).first()

            if modulo:
                # Guardar la fecha en la sesión para mostrarla en la vista de mantenimiento
                request.session[
                    'mantenimiento_hasta'] = modulo.mantenimiento_hasta.isoformat() if modulo.mantenimiento_hasta else None
                return redirect('intranet:mantenimiento')

        return self.get_response(request)
