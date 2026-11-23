from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from core.models.establecimientos import Establecimiento as Organizacion
from core.models.usuarios import User
from .models import AsignacionEstacion, Computador, Monitor, Producto, Marca, Modelo, FuncionarioInventario
from .models.mantenedores import Establecimiento, JefeTic, TipoProducto


class EstacionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = Organizacion.objects.create(nombre='Organización')
        cls.user = User.objects.create_user(username='estaciones', establecimiento=cls.org)
        cls.marca = Marca.objects.create(nombre='Marca', establecimiento=cls.org)
        cls.modelo = Modelo.objects.create(nombre='Modelo', marca=cls.marca, establecimiento=cls.org)
        cls.destino = Establecimiento.objects.create(nombre='Destino', establecimiento=cls.org)
        cls.jefe = JefeTic.objects.create(nombre='Jefe', establecimiento=cls.org)
        cls.responsable = FuncionarioInventario.objects.create(nombre='Responsable', establecimiento=cls.org)
        cls.tipo = TipoProducto.objects.create(nombre='Teclado', establecimiento=cls.org)
        cls.producto = Producto.objects.create(nombre='Teclado USB', tipo_producto=cls.tipo,
                                              stock_total=5, stock_disponible=5, establecimiento=cls.org)
        cls.monitor = Monitor.objects.create(numero_serie='MON-EST', marca=cls.marca, modelo=cls.modelo, establecimiento=cls.org)
        cls.pc = Computador.objects.create(numero_serie='PC-EST', marca=cls.marca, modelo=cls.modelo,
                                           formato='NOTEBOOK', establecimiento=cls.org)

    def setUp(self):
        self.client.force_login(self.user)
        self.url = reverse('inventario_tic:estacion_create')

    def datos(self, tipo, ids):
        data = {
            'destino-establecimiento_mantenedor': self.destino.pk,
            'destino-responsable': self.responsable.pk, 'destino-jefe_entrega': self.jefe.pk,
            f'incluir_{tipo}': 'on', f'{tipo}-TOTAL_FORMS': len(ids), f'{tipo}-INITIAL_FORMS': 0,
        }
        for i, pk in enumerate(ids):
            data[f'{tipo}-{i}-existente'] = pk
            if tipo == 'productos':
                data[f'{tipo}-{i}-cantidad'] = 1
        return data

    def test_formulario_y_solo_monitor_con_actas_individuales(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        response = self.client.post(self.url, self.datos('monitores', [self.monitor.pk]))
        self.assertEqual(response.status_code, 302)
        self.monitor.refresh_from_db()
        self.assertTrue(self.monitor.asignado)
        self.assertEqual(self.monitor.responsable, self.responsable)
        entrega = AsignacionEstacion.objects.get()
        self.assertContains(self.client.get(response.url), 'Acta del monitor')
        self.assertEqual(len(entrega.contenido['items']), 1)
        # La consulta del acta individual original funciona sin cambiar su vista.
        with patch('inventario_tic.views.pdfs.HTML') as html:
            response = self.client.get(reverse('inventario_tic:generar_acta_monitores', args=[self.monitor.pk]))
        self.assertEqual(response.status_code, 200)
        html.return_value.write_pdf.assert_called_once()

    def test_solo_productos_descontar_y_acta_inmutable(self):
        data = self.datos('productos', [self.producto.pk])
        data['productos-0-cantidad'] = 2
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_disponible, 3)
        entrega = AsignacionEstacion.objects.get()
        self.assertEqual(entrega.productos.get().cantidad, 2)
        self.responsable.nombre = 'Nombre modificado'
        self.responsable.save()
        self.assertEqual(entrega.contenido['responsable'], 'Responsable')
        with patch('weasyprint.HTML') as html:
            response = self.client.get(reverse('inventario_tic:estacion_acta', args=[entrega.pk]))
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('TECLADO USB', html.call_args.kwargs['string'])

    def test_exige_elemento_e_ignora_seccion_desmarcada(self):
        data = self.datos('monitores', [self.monitor.pk])
        data['computador-TOTAL_FORMS'] = 'inválido'
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        data.pop('incluir_monitores')
        self.assertContains(self.client.post(self.url, data), 'Debe incluir al menos')

    def test_duplicados_limites_y_cantidades_invalidas(self):
        for tipo, ids in [('monitores', [self.monitor.pk] * 2), ('monitores', [self.monitor.pk] * 3),
                          ('computador', [self.pc.pk] * 2), ('productos', [self.producto.pk] * 2)]:
            with self.subTest(tipo=tipo, count=len(ids)):
                self.assertEqual(self.client.post(self.url, self.datos(tipo, ids)).status_code, 200)
        for cantidad in (0, -1, 6):
            data = self.datos('productos', [self.producto.pk])
            data['productos-0-cantidad'] = cantidad
            response = self.client.post(self.url, data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['activa'], 'productos')
        self.assertFalse(AsignacionEstacion.objects.exists())

    def test_rollback_si_falla_stock_despues_de_asignar_equipo(self):
        data = self.datos('computador', [self.pc.pk])
        productos = self.datos('productos', [self.producto.pk])
        data.update(productos)
        data['productos-0-cantidad'] = 99
        self.assertContains(self.client.post(self.url, data), 'Stock insuficiente')
        self.pc.refresh_from_db()
        self.assertFalse(self.pc.asignado)
        self.assertFalse(AsignacionEstacion.objects.exists())

    def test_busqueda_y_post_excluyen_asignados_y_otra_organizacion(self):
        self.monitor.asignado = True
        self.monitor.save()
        response = self.client.get(reverse('inventario_tic:estacion_buscar'), {'tipo': 'monitores', 'q': 'MON-EST'})
        self.assertEqual(response.json()['results'], [])
        self.assertEqual(self.client.post(self.url, self.datos('monitores', [self.monitor.pk])).status_code, 200)
        otra = Organizacion.objects.create(nombre='Otra')
        self.monitor.asignado = False
        self.monitor.establecimiento = otra
        self.monitor.save()
        response = self.client.get(reverse('inventario_tic:estacion_buscar'), {'tipo': 'monitores'})
        self.assertEqual(response.json()['results'], [])
        self.assertEqual(self.client.post(self.url, self.datos('monitores', [self.monitor.pk])).status_code, 200)

    def test_crear_producto_nuevo_con_stock_al_confirmar(self):
        data = self.datos('productos', [''])
        data.update({'productos-0-nuevo': 'True', 'productos-0-registro-nombre': 'Mouse',
                     'productos-0-registro-tipo_producto': self.tipo.pk,
                     'productos-0-registro-stock_total': 8, 'productos-0-registro-stock_disponible': 8,
                     'productos-0-registro-stock_minimo': 1, 'productos-0-cantidad': 3})
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        mouse = Producto.objects.get(nombre='MOUSE')
        self.assertEqual(mouse.stock_disponible, 5)
        self.assertEqual(mouse.establecimiento, self.org)

    def test_equipo_nuevo_errores_conservan_datos_y_no_crean(self):
        data = self.datos('monitores', [''])
        data.update({'monitores-0-nuevo': 'True', 'monitores-0-registro-numero_serie': 'nuevo-123',
                     'monitores-0-registro-marca': self.marca.pk, 'monitores-0-registro-modelo': self.modelo.pk})
        data['destino-responsable'] = ''
        response = self.client.post(self.url, data)
        self.assertContains(response, 'NUEVO-123')
        self.assertFalse(Monitor.objects.filter(numero_serie='NUEVO-123').exists())
        data['destino-responsable'] = self.responsable.pk
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        self.assertTrue(Monitor.objects.get(numero_serie='NUEVO-123').asignado)

    def test_funcionario_modal_se_guarda_inmediatamente(self):
        response = self.client.post(reverse('inventario_tic:funcionario_create_modal'), {'nombre': 'Nuevo funcionario'})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(FuncionarioInventario.objects.filter(pk=response.json()['id']).exists())
        self.assertFalse(AsignacionEstacion.objects.exists())

    def test_estacion_completa_dos_monitores_y_computador(self):
        segundo = Monitor.objects.create(numero_serie='MON-EST-2', marca=self.marca, modelo=self.modelo, establecimiento=self.org)
        data = self.datos('computador', [self.pc.pk])
        data.update(self.datos('monitores', [self.monitor.pk, segundo.pk]))
        data.update(self.datos('productos', [self.producto.pk]))
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        self.assertEqual(len(AsignacionEstacion.objects.get().contenido['items']), 4)
        self.assertEqual(Monitor.objects.filter(asignado=True).count(), 2)
        self.pc.refresh_from_db()
        self.assertTrue(self.pc.asignado)
        self.assertEqual(self.pc.jefe_entrega, self.jefe)

    def test_nuevos_no_persisten_si_falla_otra_seccion(self):
        data = self.datos('computador', [''])
        data.update({'computador-0-nuevo': 'True', 'computador-0-registro-numero_serie': 'NUEVO-ROLLBACK',
                     'computador-0-registro-marca': self.marca.pk, 'computador-0-registro-modelo': self.modelo.pk,
                     'computador-0-registro-formato': 'NOTEBOOK'})
        data.update(self.datos('productos', [self.producto.pk]))
        data['productos-0-cantidad'] = 99
        self.assertEqual(self.client.post(self.url, data).status_code, 200)
        self.assertFalse(Computador.objects.filter(numero_serie='NUEVO-ROLLBACK').exists())
        self.assertFalse(AsignacionEstacion.objects.exists())

    def test_acta_conjunta_pdf_real(self):
        response = self.client.post(self.url, self.datos('productos', [self.producto.pk]))
        self.assertEqual(response.status_code, 302)
        entrega = AsignacionEstacion.objects.get()
        response = self.client.get(reverse('inventario_tic:estacion_acta', args=[entrega.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF-'))

    def test_catalogos_y_entregas_aislados(self):
        response = self.client.post(self.url, self.datos('productos', [self.producto.pk]))
        self.assertEqual(response.status_code, 302)
        otra = Organizacion.objects.create(nombre='Otra')
        self.user.establecimiento = otra
        self.user.save()
        self.assertEqual(self.client.get(response.url).status_code, 404)
        data = self.datos('productos', [self.producto.pk])
        self.assertEqual(self.client.post(self.url, data).status_code, 200)

    def test_datatable_paginacion_busqueda_y_orden_por_datos_del_acta(self):
        for nombre in ('Ana', 'Beatriz', 'Carolina'):
            AsignacionEstacion.objects.create(
                establecimiento=self.org, destino=self.destino, responsable=self.responsable,
                jefe_entrega=self.jefe, created_by=self.user,
                contenido={'destino': 'Destino histórico', 'responsable': nombre, 'items': []})
        url = reverse('inventario_tic:estacion_list')
        self.assertContains(self.client.get(url), 'estaciones_datatable.js')
        params = {'action': 'search', 'draw': 3, 'start': 1, 'length': 1,
                  'order[0][column]': 3, 'order[0][dir]': 'asc'}
        resultado = self.client.post(url, params).json()
        self.assertEqual(resultado['draw'], 3)
        self.assertEqual(resultado['recordsTotal'], 3)
        self.assertEqual(resultado['recordsFiltered'], 3)
        self.assertEqual([fila['responsable'] for fila in resultado['data']], ['Beatriz'])
        self.assertIn('acta_url', resultado['data'][0])
        params.update({'start': 0, 'search[value]': 'Carolina'})
        resultado = self.client.post(url, params).json()
        self.assertEqual(resultado['recordsTotal'], 3)
        self.assertEqual(resultado['recordsFiltered'], 1)
        self.assertEqual(resultado['data'][0]['responsable'], 'Carolina')
        params.update({'search[value]': 'histórico', 'length': -1, 'order[0][column]': 2})
        self.assertEqual(len(self.client.post(url, params).json()['data']), 3)

    def test_datatable_respeta_organizacion_y_parametros_invalidos(self):
        self.client.post(self.url, self.datos('productos', [self.producto.pk]))
        url = reverse('inventario_tic:estacion_list')
        self.assertEqual(self.client.post(url, {'action': 'otra'}).status_code, 400)
        params = {'action': 'search', 'draw': 'no-numero', 'start': -3,
                  'length': 'no-numero', 'order[0][column]': 'desconocido'}
        self.assertEqual(self.client.post(url, params).json()['recordsTotal'], 1)
        self.user.establecimiento = Organizacion.objects.create(nombre='Otra')
        self.user.save()
        resultado = self.client.post(url, params).json()
        self.assertEqual(resultado['recordsTotal'], 0)
        self.assertEqual(resultado['data'], [])
