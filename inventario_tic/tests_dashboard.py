from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models.establecimientos import Establecimiento as Organizacion
from .models import AsignacionEstacion, ProductoAsignadoEstacion
from .models.mantenedores import Establecimiento
from . import tests_asignados as datos_asignados


class DashboardTests(TestCase):
    setUpTestData = classmethod(datos_asignados.AsignadosTests.setUpTestData.__func__)
    entregar = datos_asignados.AsignadosTests.entregar

    def setUp(self):
        self.client.force_login(self.user)
        self.url = reverse('inventario_tic:dashboard_datos')
        hoy = timezone.now().date()
        self.params = {'desde': (hoy - timedelta(days=32)).isoformat(), 'hasta': hoy.isoformat()}

    def datos(self, bloque, **kwargs):
        response = self.client.get(self.url, {**self.params, 'bloque': bloque, **kwargs})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_pagina_y_widgets_inventario_actual(self):
        pagina = self.client.get(reverse('inventario_tic:dashboard'))
        self.assertContains(pagina, 'dashboard.js')
        self.entregar(2, responsable=self.otro)
        data = self.datos('inventario')
        self.assertEqual(data['widgets']['monitores'], 1)  # Monitor disponible de la fixture.
        self.assertEqual(data['widgets']['asignados'], 3)
        self.assertEqual(data['widgets']['funcionarios'], 2)
        self.assertEqual(data['porcentaje'], 75)
        self.assertEqual(data['distribucion'][0]['cantidad'], 3)
        self.monitor.asignado = False
        self.monitor.responsable = None
        self.monitor.save()
        self.assertEqual(self.datos('inventario')['widgets']['monitores'], 2)

    def test_stock_actual_independiente_del_destino_y_periodo(self):
        self.producto.stock_minimo = 2
        self.producto.stock_disponible = 0
        self.producto.save()
        data = self.datos('stock', destino=self.destino.pk)
        self.assertEqual(data['widgets'], {'stock_bajo': 1, 'agotados': 1})
        self.assertEqual(data['alertas'][0]['stock_minimo'], 2)
        self.assertEqual(data['reposicion'][0]['nombre'], self.producto.nombre)

    def test_actividad_periodo_sumatorias_y_meses_vacios(self):
        self.entregar(2)
        self.entregar(3)
        data = self.datos('actividad')
        self.assertEqual(data['widgets']['entregas_mes'], 2)
        self.assertEqual(sum(m['cantidad'] for m in data['evolucion']), 2)
        self.assertTrue(any(m['cantidad'] == 0 for m in data['evolucion']))
        self.assertEqual(data['productos'][0]['cantidad'], 5)
        self.assertEqual(len(data['ultimas']), 2)
        pasado = self.params['desde']
        data = self.datos('actividad', hasta=pasado)
        self.assertEqual(data['productos'], [])
        self.assertEqual(data['ultimas'], [])
        self.assertEqual(data['widgets']['entregas_mes'], 2)  # Mes actual, no período.

    def test_filtro_destino_y_permisos_en_todos_los_bloques(self):
        destino = Establecimiento.objects.create(nombre='Consultorio', establecimiento=self.org)
        self.entregar(2)
        self.entregar(3, destino=destino, responsable=self.otro)
        data = self.datos('actividad', destino=destino.pk)
        self.assertEqual(data['productos'][0]['cantidad'], 3)
        data = self.datos('inventario', destino=destino.pk)
        self.assertEqual(data['widgets']['asignados'], 0)
        self.assertEqual(data['widgets']['funcionarios'], 1)
        otra = Organizacion.objects.create(nombre='Otra')
        self.user.establecimiento = otra
        self.user.save()
        self.assertEqual(self.datos('inventario')['widgets']['asignados'], 0)
        self.assertEqual(self.datos('stock')['alertas'], [])
        self.assertEqual(self.datos('actividad')['productos'], [])
        for bloque in ('stock', 'actividad', 'inventario'):
            self.assertEqual(self.client.get(self.url, {**self.params, 'bloque': bloque, 'destino': destino.pk}).status_code, 400)
        self.user.establecimiento = None
        self.user.save()
        self.assertEqual(self.datos('actividad')['ultimas'], [])
        self.user.is_superuser = True
        self.user.save()
        self.assertEqual(self.datos('actividad')['productos'][0]['cantidad'], 5)

    def test_validacion_autenticacion_y_solo_lectura(self):
        for params in ({'bloque': 'incorrecto'}, {'bloque': 'stock', 'desde': 'mal'},
                       {'bloque': 'actividad', 'desde': '2026-12-01', 'hasta': '2026-01-01'},
                       {'bloque': 'inventario', 'destino': 'abc'}):
            self.assertEqual(self.client.get(self.url, {**self.params, **params}).status_code, 400)
        self.assertEqual(self.client.post(self.url).status_code, 405)
        self.assertFalse(AsignacionEstacion.objects.exists())
        self.assertFalse(ProductoAsignadoEstacion.objects.exists())
        self.client.logout()
        self.assertEqual(self.client.get(self.url, self.params).status_code, 302)
