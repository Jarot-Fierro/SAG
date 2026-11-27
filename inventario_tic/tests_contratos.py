from datetime import timedelta
from unittest.mock import patch

from django.test import RequestFactory, TestCase
from django.urls import resolve, reverse
from django.utils import timezone

from core.models.establecimientos import Establecimiento as Organizacion
from core.models.unidad_organizacional import UnidadOrganizacional
from . import tests_asignados as datos_asignados
from .forms.computadores import FormComputador
from .forms.monitores import FormMonitor
from .forms.celulares import FormCelular
from .forms.impresora import FormImpresora
from .middleware import AlertasContratosMiddleware, CONTRATOS_AVISO_SESION, alertas_contratos
from .models import Celular, Computador, Impresora, Monitor
from .models.mantenedores import Contrato


class ContratosTests(TestCase):
    setUpTestData = classmethod(datos_asignados.AsignadosTests.setUpTestData.__func__)

    def setUp(self):
        self.client.force_login(self.user)
        self.hoy = timezone.now().date()
        self.contrato = Contrato.objects.create(nombre='Contrato de equipos', establecimiento=self.org,
                                                fecha_vencimiento=self.hoy + timedelta(days=5), dias_aviso=5)
        for model in (Celular, Computador, Monitor):
            model.objects.filter(establecimiento=self.org).update(contrato=self.contrato)

    def test_cuenta_activos_asignados_y_disponibles_cuatro_tipos(self):
        departamento = UnidadOrganizacional.objects.create(nombre='TI', establecimiento=self.org)
        Impresora.objects.create(numero_serie='IMP-CONTRATO', hh='HH', marca=self.monitor.marca,
                                 modelo=self.monitor.modelo, departamento=departamento,
                                 establecimiento=self.org, contrato=self.contrato)
        alertas = alertas_contratos(self.user)
        self.assertEqual(len(alertas), 1)
        self.assertEqual(alertas[0]['total'], 5)
        self.assertEqual(alertas[0]['cantidades'], {'Celulares': 1, 'Computadores': 1, 'Monitores': 2, 'Impresoras': 1})
        self.assertEqual(alertas[0]['dias'], 5)
        self.assertEqual(alertas[0]['estado'], 'Vence en 5 días')
        Monitor.objects.filter(pk=self.monitor.pk).update(is_active=False)
        self.assertEqual(alertas_contratos(self.user)[0]['total'], 4)

    def test_umbral_hoy_vencido_y_desactivar_desde_mantenedor(self):
        for dias, cantidad in ((6, 0), (5, 1), (0, 1), (-10, 1)):
            self.contrato.fecha_vencimiento = self.hoy + timedelta(days=dias)
            self.contrato.save()
            self.assertEqual(len(alertas_contratos(self.user)), cantidad)
        url = reverse('inventario_tic:monitor_list')
        self.assertContains(self.client.get(url), 'contratosVencimientoModal')
        response = self.client.post(reverse('inventario_tic:contrato_update', args=[self.contrato.pk]), {
            'nombre': self.contrato.nombre, 'fecha_vencimiento': self.contrato.fecha_vencimiento.isoformat(),
            'dias_aviso': 5,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(alertas_contratos(self.user), [])
        self.assertNotContains(self.client.get(url), 'contratosVencimientoModal')

    def test_excluye_inactivos_sin_fecha_sin_equipos_y_otra_organizacion(self):
        self.contrato.notificar_vencimiento = False
        self.contrato.save()
        self.assertEqual(alertas_contratos(self.user), [])
        self.contrato.notificar_vencimiento = True
        self.contrato.is_active = False
        self.contrato.save()
        self.assertEqual(alertas_contratos(self.user), [])
        self.contrato.is_active = True
        self.contrato.fecha_vencimiento = None
        self.contrato.save()
        self.assertEqual(alertas_contratos(self.user), [])
        self.contrato.fecha_vencimiento = self.hoy
        self.contrato.save()
        otra = Organizacion.objects.create(nombre='Otra')
        self.user.establecimiento = otra
        self.user.save()
        self.assertEqual(alertas_contratos(self.user), [])
        self.user.is_superuser = True
        self.user.save()
        self.assertEqual(len(alertas_contratos(self.user)), 1)

    def test_middleware_perezoso_no_consulta_ajax_ni_otro_modulo(self):
        factory = RequestFactory()
        middleware = AlertasContratosMiddleware(lambda r: None)
        url = reverse('inventario_tic:monitor_list')
        for headers in ({'HTTP_ACCEPT': 'application/json'}, {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}):
            request = factory.get(url, **headers)
            request.user = self.user
            request.resolver_match = resolve(url)
            with self.assertNumQueries(0):
                middleware.process_view(request, None, (), {})
            self.assertFalse(hasattr(request, 'alertas_contratos'))
        request = factory.get(url)
        request.session = {}
        request.user = self.user
        request.resolver_match = resolve(url)
        with self.assertNumQueries(0):
            middleware.process_view(request, None, (), {})
        self.assertTrue(bool(request.alertas_contratos))
        request.resolver_match = None
        request2 = factory.get('/')
        request2.user = self.user
        request2.resolver_match = None
        middleware.process_view(request2, None, (), {})
        self.assertFalse(hasattr(request2, 'alertas_contratos'))

    def test_modal_una_vez_por_login_y_boton_disponible_al_navegar(self):
        url = reverse('inventario_tic:monitor_list')
        self.assertNotIn(CONTRATOS_AVISO_SESION, self.client.session)
        self.assertContains(self.client.get(url), 'data-autoabrir="true"')
        self.assertTrue(self.client.session[CONTRATOS_AVISO_SESION])
        siguiente = self.client.get(reverse('inventario_tic:computador_list'))
        self.assertContains(siguiente, 'data-autoabrir="false"')
        self.assertContains(siguiente, 'Contratos con aviso')
        session = self.client.session
        session.set_expiry(48 * 60 * 60)
        session.save()
        with patch('inventario_tic.middleware.timezone.now', return_value=timezone.now() + timedelta(hours=20)):
            self.assertContains(self.client.get(url), 'data-autoabrir="false"')
        # También se reinicia al autenticar otra vez al mismo usuario sin vaciar antes la sesión.
        self.client.force_login(self.user)
        self.assertNotIn(CONTRATOS_AVISO_SESION, self.client.session)
        self.assertContains(self.client.get(url), 'data-autoabrir="true"')
        self.client.logout()
        self.client.force_login(self.user)
        self.assertContains(self.client.get(url), 'data-autoabrir="true"')

    def test_ajax_json_pdf_y_otro_modulo_no_consumen_aviso(self):
        url = reverse('inventario_tic:monitor_list')
        self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertNotIn(CONTRATOS_AVISO_SESION, self.client.session)
        self.client.get(reverse('inventario_tic:dashboard_datos'), {'bloque': 'stock'})
        self.assertNotIn(CONTRATOS_AVISO_SESION, self.client.session)
        with patch('inventario_tic.views.pdfs.HTML'):
            self.client.get(reverse('inventario_tic:generar_acta_monitores', args=[self.monitor.pk]))
        self.assertNotIn(CONTRATOS_AVISO_SESION, self.client.session)
        request = RequestFactory().get('/')
        request.user = self.user
        request.session = self.client.session
        request.resolver_match = None
        AlertasContratosMiddleware(lambda r: None).process_view(request, None, (), {})
        self.assertNotIn(CONTRATOS_AVISO_SESION, request.session)
        self.assertContains(self.client.get(url), 'data-autoabrir="true"')

    def test_primera_entrada_sin_avisos_no_interrumpe_despues(self):
        url = reverse('inventario_tic:monitor_list')
        self.contrato.notificar_vencimiento = False
        self.contrato.save()
        self.assertNotContains(self.client.get(url), 'contratosVencimientoModal')
        self.assertTrue(self.client.session[CONTRATOS_AVISO_SESION])
        self.contrato.notificar_vencimiento = True
        self.contrato.save()
        self.assertContains(self.client.get(url), 'data-autoabrir="false"')
        self.client.force_login(self.user)
        self.assertContains(self.client.get(url), 'data-autoabrir="true"')

    def test_formularios_opcionales_y_separacion_por_establecimiento(self):
        otra = Organizacion.objects.create(nombre='Otra')
        ajeno = Contrato.objects.create(nombre='Ajeno', establecimiento=otra)
        request = RequestFactory().get('/')
        request.user = self.user
        for form_class in (FormComputador, FormMonitor, FormCelular, FormImpresora):
            form = form_class(request=request)
            self.assertFalse(form.fields['contrato'].required)
            self.assertIn(self.contrato, form.fields['contrato'].queryset)
            self.assertNotIn(ajeno, form.fields['contrato'].queryset)
            form = form_class({'contrato': ajeno.pk}, request=request)
            form.is_valid()
            self.assertIn('contrato', form.errors)
        data = {'numero_serie': 'NUEVO-CONTRATO', 'marca': self.monitor.marca_id,
                'modelo': self.monitor.modelo_id, 'contrato': self.contrato.pk}
        response = self.client.post(reverse('inventario_tic:monitor_create'), data)
        self.assertEqual(response.status_code, 302)
        nuevo = Monitor.objects.get(numero_serie='NUEVO-CONTRATO')
        self.assertEqual(nuevo.contrato, self.contrato)
        self.assertEqual(nuevo.history.first().contrato_id, self.contrato.pk)
