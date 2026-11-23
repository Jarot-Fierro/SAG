from django.test import TestCase
from django.urls import reverse

from core.models.establecimientos import Establecimiento as Organizacion
from core.models.usuarios import User
from .models import (AsignacionEstacion, Celular, Computador, FuncionarioInventario,
                     Marca, Modelo, Monitor, Producto, ProductoAsignadoEstacion)
from .models.mantenedores import Establecimiento, JefeTic, TipoProducto


class AsignadosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = Organizacion.objects.create(nombre='Organización')
        cls.user = User.objects.create_user(username='consulta', establecimiento=cls.org)
        cls.destino = Establecimiento.objects.create(nombre='Hospital', establecimiento=cls.org)
        cls.responsable = FuncionarioInventario.objects.create(nombre='Ana', establecimiento=cls.org)
        cls.otro = FuncionarioInventario.objects.create(nombre='Pedro', establecimiento=cls.org)
        cls.jefe = JefeTic.objects.create(nombre='Jefe', establecimiento=cls.org)
        marca = Marca.objects.create(nombre='Marca', establecimiento=cls.org)
        modelo = Modelo.objects.create(nombre='Modelo', marca=marca, establecimiento=cls.org)
        comun = dict(establecimiento=cls.org, responsable=cls.responsable, establecimiento_mantenedor=cls.destino,
                     marca=marca, modelo=modelo, asignado=True)
        cls.monitor = Monitor.objects.create(numero_serie='MON-1', **comun)
        Computador.objects.create(numero_serie='PC-1', formato='NOTEBOOK', **comun)
        Celular.objects.create(imei='123456789012345', **comun)
        Monitor.objects.create(numero_serie='DEVUELTO', marca=marca, modelo=modelo, establecimiento=cls.org)
        tipo = TipoProducto.objects.create(nombre='Teclado', establecimiento=cls.org)
        cls.producto = Producto.objects.create(nombre='Teclado USB', tipo_producto=tipo, establecimiento=cls.org)

    def setUp(self):
        self.client.force_login(self.user)
        self.url = reverse('inventario_tic:asignados_list')

    def entregar(self, cantidad, responsable=None, destino=None, org=None):
        entrega = AsignacionEstacion.objects.create(
            establecimiento=org or self.org, destino=destino or self.destino,
            responsable=responsable or self.responsable, jefe_entrega=self.jefe,
            created_by=self.user, contenido={})
        ProductoAsignadoEstacion.objects.create(asignacion=entrega, producto=self.producto, cantidad=cantidad)

    def datos(self, **params):
        response = self.client.post(self.url, {'action': 'search', **params})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_equipos_vigentes_y_productos_agrupados(self):
        self.entregar(2)
        self.entregar(3)
        self.entregar(1, responsable=self.otro)
        resultado = self.datos()
        self.assertEqual(resultado['recordsTotal'], 5)
        filas = resultado['data']
        self.assertEqual({f['col_tipo'] for f in filas}, {'Monitor', 'Computador', 'Celular', 'Producto'})
        productos = {f['col_funcionario']: f['col_cantidad'] for f in filas if f['col_tipo'] == 'Producto'}
        self.assertEqual(productos, {'Ana': 5, 'Pedro': 1})
        self.assertNotIn('DEVUELTO', str(filas))
        self.assertContains(self.client.get(self.url), 'asignados_datatable.js')

    def test_busqueda_agregada_paginacion_orden_y_destinos(self):
        otro_destino = Establecimiento.objects.create(nombre='Consultorio', establecimiento=self.org)
        self.entregar(2)
        self.entregar(3, destino=otro_destino)
        producto = self.datos(**{'search[value]': 'Producto'})
        self.assertEqual(producto['recordsFiltered'], 1)
        self.assertEqual(producto['data'][0]['col_cantidad'], 5)
        self.assertEqual(producto['data'][0]['col_destino'], 'Varios establecimientos')
        self.assertTrue(any(f['col_tipo'] == 'Producto' and f['col_cantidad'] == 5
                            for f in self.datos(**{'search[value]': '5'})['data']))
        self.assertEqual(self.datos(**{'search[value]': 'MON-1'})['recordsFiltered'], 1)
        self.assertEqual(len(self.datos(start=1, length=1)['data']), 1)
        self.assertEqual(self.datos(**{'order[0][column]': 6, 'order[0][dir]': 'desc'})['data'][0]['col_cantidad'], 5)

    def test_devolucion_inactivos_y_aislamiento(self):
        self.entregar(2)
        self.monitor.asignado = False
        self.monitor.save()
        self.assertEqual(self.datos()['recordsTotal'], 3)
        self.user.establecimiento = Organizacion.objects.create(nombre='Otra')
        self.user.save()
        self.assertEqual(self.datos()['recordsTotal'], 0)
        self.user.establecimiento = None
        self.user.save()
        self.assertEqual(self.datos()['data'], [])
        self.user.is_superuser = True
        self.user.save()
        self.assertEqual(self.datos()['recordsTotal'], 3)

    def test_lectura_sin_modificaciones_y_parametros_invalidos(self):
        self.assertEqual(self.client.post(self.url, {'action': 'guardar'}).status_code, 400)
        resultado = self.datos(draw='invalido', start=-10, length='incorrecto', **{'order[0][column]': 99})
        self.assertEqual(resultado['draw'], 1)
        self.assertEqual(resultado['recordsTotal'], 3)
        self.assertFalse(AsignacionEstacion.objects.exists())
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)
