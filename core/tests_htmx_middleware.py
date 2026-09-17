from django.test import TestCase, RequestFactory
from django.http import HttpResponseRedirect
from django.conf import settings
from core.middleware import HtmxRedirectMiddleware

class HtmxRedirectMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = HtmxRedirectMiddleware(lambda r: self.response)

    def test_htmx_redirect_to_login(self):
        # Simular una respuesta de redirección al login
        self.response = HttpResponseRedirect(str(settings.LOGIN_URL))
        
        # Petición HTMX
        request = self.factory.get('/some-protected-url/', HTTP_HX_REQUEST='true')
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['HX-Redirect'], str(settings.LOGIN_URL))

    def test_non_htmx_redirect_to_login(self):
        # Simular una respuesta de redirección al login
        self.response = HttpResponseRedirect(str(settings.LOGIN_URL))
        
        # Petición NO HTMX
        request = self.factory.get('/some-protected-url/')
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('HX-Redirect', response)

    def test_htmx_redirect_to_other(self):
        # Simular una respuesta de redirección a otro sitio
        other_url = '/some-other-url/'
        self.response = HttpResponseRedirect(other_url)
        
        # Petición HTMX
        request = self.factory.get('/some-url/', HTTP_HX_REQUEST='true')
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 302)
        # Solo queremos redirigir al login (o mantenimiento) si queremos forzar la página completa.
        # En este caso, como no empieza por LOGIN_URL, no debería añadir HX-Redirect a menos que queramos que todos los redirects sean completos.
        # Pero según el requerimiento es para el caso de sesión cerrada.
        self.assertNotIn('HX-Redirect', response)
