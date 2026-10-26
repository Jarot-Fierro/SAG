from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from core.models import Establecimiento
from core.models.funcionario import Funcionario
from core.models.unidad_organizacional import UnidadOrganizacional
from gestion_tic.models import Activo, TipoActivo, MovimientoActivo, TipoMovimiento
from gestion_tic.models.catalogo import (
    Marca, Modelo, Propietario, JefeTic, Contrato, Ips
)

User = get_user_model()


class CatalogoViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.establecimiento = Establecimiento.objects.create(
            nombre="Hospital Base",
            alias="HB",
            is_active=True
        )
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            establecimiento=self.establecimiento
        )
        self.client.login(username="testuser", password="testpassword")

        # Unidad y Funcionario
        self.unidad = UnidadOrganizacional.objects.create(
            nombre="Informática y TIC",
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.funcionario = Funcionario.objects.create(
            rut="12345678-9",
            nombres="Pedro",
            apellidos="González",
            unidad_organizacional=self.unidad,
            establecimiento=self.establecimiento,
            is_active=True
        )

        # Crear registros de prueba
        self.marca1 = Marca.objects.create(
            nombre="Dell",
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.marca2 = Marca.objects.create(
            nombre="HP",
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.marca_inactiva = Marca.objects.create(
            nombre="Lenovo",
            establecimiento=self.establecimiento,
            is_active=False
        )

        self.modelo1 = Modelo.objects.create(
            nombre="OptiPlex 7090",
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.propietario1 = Propietario.objects.create(
            nombre="MINSAL",
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.jefetic1 = JefeTic.objects.create(
            nombre="Juan Perez",
            posicion="JEFE DPTO TIC",
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.contrato1 = Contrato.objects.create(
            nombre="Contrato Soporte 2026",
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.ip1 = Ips.objects.create(
            ip="192.168.1.10",
            mascara="255.255.255.0",
            gateway="192.168.1.1",
            vlan="VLAN 10",
            asignado=True,
            observacion="Servidor Principal",
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.ip2 = Ips.objects.create(
            ip="10.0.0.5",
            mascara="255.0.0.0",
            gateway="10.0.0.1",
            vlan="VLAN 20",
            asignado=False,
            observacion="Disponible",
            establecimiento=self.establecimiento,
            is_active=True
        )

        self.tipo_activo1 = TipoActivo.objects.create(
            nombre="Computador",
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.activo1 = Activo.objects.create(
            codigo_barra="ACT-001",
            tipo=self.tipo_activo1,
            marca=self.marca1,
            modelo=self.modelo1,
            serie="SN123456",
            contrato=self.contrato1,
            observacion="Equipo principal",
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.activo2 = Activo.objects.create(
            codigo_barra="ACT-002",
            tipo=self.tipo_activo1,
            marca=self.marca2,
            modelo=self.modelo1,
            serie="SN654321",
            contrato=self.contrato1,
            observacion="Equipo secundario",
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.activo_inactivo = Activo.objects.create(
            codigo_barra="ACT-003",
            tipo=self.tipo_activo1,
            marca=self.marca1,
            modelo=self.modelo1,
            serie="SN999999",
            contrato=self.contrato1,
            observacion="Equipo inactivo",
            establecimiento=self.establecimiento,
            is_active=False
        )

    def test_marca_list_get(self):
        url = reverse('gestion_tic:marca_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gestion_tic/catalogo/catalogo_list.html')
        self.assertIn('create_url', response.context)
        self.assertIn('edit_url_template', response.context)
        self.assertIn('delete_url_template', response.context)

    def test_marca_datatable_search_post(self):
        url = reverse('gestion_tic:marca_list')
        response = self.client.post(url, {
            'action': 'search',
            'draw': 1,
            'start': 0,
            'length': 10,
            'search[value]': ''
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['draw'], 1)
        self.assertEqual(data['recordsTotal'], 2)  # Excluye la inactiva
        self.assertEqual(data['recordsFiltered'], 2)
        nombres = [item['nombre'] for item in data['data']]
        self.assertIn('DELL', nombres)
        self.assertIn('HP', nombres)

    def test_marca_datatable_search_filter(self):
        url = reverse('gestion_tic:marca_list')
        response = self.client.post(url, {
            'action': 'search',
            'draw': 1,
            'start': 0,
            'length': 10,
            'search[value]': 'Dell'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['recordsFiltered'], 1)
        self.assertEqual(data['data'][0]['nombre'], 'DELL')

    def test_marca_create(self):
        url = reverse('gestion_tic:marca_create')
        response = self.client.post(url, {
            'nombre': 'Apple'
        })
        self.assertEqual(response.status_code, 302)
        nueva_marca = Marca.objects.get(nombre='APPLE')
        self.assertTrue(nueva_marca.is_active)
        self.assertEqual(nueva_marca.establecimiento, self.establecimiento)

    def test_marca_update(self):
        url = reverse('gestion_tic:marca_update', kwargs={'pk': self.marca1.pk})
        response = self.client.post(url, {
            'nombre': 'Dell Enterprise'
        })
        self.assertEqual(response.status_code, 302)
        self.marca1.refresh_from_db()
        self.assertEqual(self.marca1.nombre, 'DELL ENTERPRISE')

    def test_marca_deactivate_ajax(self):
        url = reverse('gestion_tic:marca_deactivate', kwargs={'pk': self.marca1.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 'success')
        self.marca1.refresh_from_db()
        self.assertFalse(self.marca1.is_active)  # Desactivación lógica, no física
        self.assertTrue(Marca.objects.filter(pk=self.marca1.pk).exists())

    def test_jefetic_list_and_search(self):
        url = reverse('gestion_tic:jefetic_list')
        response = self.client.post(url, {
            'action': 'search',
            'draw': 1,
            'start': 0,
            'length': 10,
            'search[value]': 'TIC'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['recordsFiltered'], 1)
        self.assertEqual(data['data'][0]['posicion'], 'JEFE DPTO TIC')

    def test_contrato_list(self):
        url = reverse('gestion_tic:contrato_list')
        response = self.client.post(url, {
            'action': 'search',
            'draw': 1,
            'start': 0,
            'length': 10,
            'search[value]': ''
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['recordsTotal'], 1)
        self.assertEqual(data['data'][0]['nombre'], 'CONTRATO SOPORTE 2026')

    def test_ips_list_and_segment_filter(self):
        url = reverse('gestion_tic:ips_list')
        # Filtro de segmento específico
        response = self.client.post(url, {
            'action': 'search',
            'draw': 1,
            'start': 0,
            'length': 10,
            'segmento': '192.168.1.x',
            'search[value]': ''
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['recordsFiltered'], 1)
        self.assertEqual(data['data'][0]['ip'], '192.168.1.10')

    def test_ips_deactivate_ajax(self):
        url = reverse('gestion_tic:ips_deactivate', kwargs={'pk': self.ip1.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.ip1.refresh_from_db()
        self.assertFalse(self.ip1.is_active)
        self.assertTrue(Ips.objects.filter(pk=self.ip1.pk).exists())

    def test_activo_list_get(self):
        url = reverse('gestion_tic:activo_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gestion_tic/activos/activo_list.html')
        self.assertIn('create_url', response.context)
        self.assertIn('edit_url_template', response.context)
        self.assertIn('delete_url_template', response.context)

    def test_activo_datatable_search_post(self):
        url = reverse('gestion_tic:activo_list')
        response = self.client.post(url, {
            'action': 'search',
            'draw': 1,
            'start': 0,
            'length': 10,
            'search[value]': ''
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['draw'], 1)
        self.assertEqual(data['recordsTotal'], 2)  # Excluye el inactivo
        self.assertEqual(data['recordsFiltered'], 2)
        codigos = [item['codigo_barra'] for item in data['data']]
        self.assertIn('ACT-001', codigos)
        self.assertIn('ACT-002', codigos)

    def test_activo_datatable_filter_marca_and_codigo(self):
        url = reverse('gestion_tic:activo_list')
        response = self.client.post(url, {
            'action': 'search',
            'draw': 1,
            'start': 0,
            'length': 10,
            'codigo_barra': 'ACT-001',
            'search[value]': ''
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['recordsFiltered'], 1)
        self.assertEqual(data['data'][0]['codigo_barra'], 'ACT-001')

    def test_activo_create(self):
        url = reverse('gestion_tic:activo_create')
        response = self.client.post(url, {
            'codigo_barra': 'ACT-004',
            'tipo': self.tipo_activo1.pk,
            'marca': self.marca1.pk,
            'modelo': self.modelo1.pk,
            'serie': 'SNNEW999',
            'contrato': self.contrato1.pk,
            'observacion': 'Nuevo equipo creado en test'
        })
        self.assertEqual(response.status_code, 302)
        nuevo_activo = Activo.objects.get(codigo_barra='ACT-004')
        self.assertTrue(nuevo_activo.is_active)
        self.assertEqual(nuevo_activo.establecimiento, self.establecimiento)
        self.assertEqual(nuevo_activo.serie, 'SNNEW999')

    def test_activo_update(self):
        url = reverse('gestion_tic:activo_update', kwargs={'pk': self.activo1.pk})
        response = self.client.post(url, {
            'codigo_barra': 'ACT-001-MOD',
            'tipo': self.tipo_activo1.pk,
            'marca': self.marca1.pk,
            'modelo': self.modelo1.pk,
            'serie': 'SN123456-UPD',
            'contrato': self.contrato1.pk,
            'observacion': 'Equipo modificado'
        })
        self.assertEqual(response.status_code, 302)
        self.activo1.refresh_from_db()
        self.assertEqual(self.activo1.codigo_barra, 'ACT-001-MOD')
        self.assertEqual(self.activo1.serie, 'SN123456-UPD')

    def test_activo_deactivate_ajax(self):
        url = reverse('gestion_tic:activo_deactivate', kwargs={'pk': self.activo1.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.activo1.refresh_from_db()
        self.assertFalse(self.activo1.is_active)  # Desactivación lógica
        self.assertTrue(Activo.objects.filter(pk=self.activo1.pk).exists())

    def test_movimientos_activo_list_get_and_search(self):
        url = reverse('gestion_tic:movimientos_activo_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gestion_tic/activos/movimientos_activo_list.html')

        # DataTables search
        response_dt = self.client.post(url, {
            'action': 'search',
            'draw': 1,
            'start': 0,
            'length': 10,
            'search[value]': ''
        })
        self.assertEqual(response_dt.status_code, 200)
        data = response_dt.json()
        self.assertEqual(data['draw'], 1)
        self.assertEqual(data['recordsTotal'], 2)
        codigos = [item['codigo_barra'] for item in data['data']]
        self.assertIn('ACT-001', codigos)

    def test_equipos_baja_cart_flow_and_datatable(self):
        url = reverse('gestion_tic:equipos_baja')
        # 1. GET view
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gestion_tic/activos/equipos_baja.html')

        # 2. DataTables search
        res_search = self.client.post(url, {
            'action': 'search',
            'draw': 1,
            'start': 0,
            'length': 10,
            'search[value]': ''
        })
        self.assertEqual(res_search.status_code, 200)
        data = res_search.json()
        self.assertEqual(data['recordsTotal'], 2)

        # 3. Add to cart AJAX
        res_add = self.client.post(url, {
            'action': 'add',
            'activo_id': self.activo1.pk,
            'is_ajax': 'true'
        })
        self.assertEqual(res_add.status_code, 200)
        self.assertTrue(res_add.json()['success'])
        self.assertEqual(res_add.json()['cart_count'], 1)

        # Verify excluded from DataTables
        res_search_after_add = self.client.post(url, {
            'action': 'search',
            'draw': 2,
            'start': 0,
            'length': 10,
            'search[value]': ''
        })
        data_after = res_search_after_add.json()
        self.assertEqual(data_after['recordsTotal'], 1)

        # 4. Remove from cart AJAX
        res_remove = self.client.post(url, {
            'action': 'remove',
            'activo_id': self.activo1.pk,
            'is_ajax': 'true'
        })
        self.assertEqual(res_remove.status_code, 200)
        self.assertEqual(res_remove.json()['cart_count'], 0)

        # 5. Add and Process bulk baja
        self.client.post(url, {
            'action': 'add',
            'activo_id': self.activo1.pk,
            'is_ajax': 'true'
        })
        res_proc = self.client.post(url, {
            'action': 'procesar',
            'is_ajax': 'true'
        })
        self.assertEqual(res_proc.status_code, 200)
        self.assertTrue(res_proc.json()['success'])
        self.activo1.refresh_from_db()
        self.assertTrue(self.activo1.de_baja)

    def test_activo_list_asignado_get_and_search(self):
        # Crear tipo movimiento y asignar activo a funcionario
        tipo_mov = TipoMovimiento.objects.create(
            nombre="Asignación",
            establecimiento=self.establecimiento,
            is_active=True
        )
        mov = MovimientoActivo.objects.create(
            activo=self.activo2,
            tipo_movimiento=tipo_mov,
            funcionario=self.funcionario,
            ip=self.ip1,
            establecimiento=self.establecimiento
        )

        url = reverse('gestion_tic:activo_list_asignado')
        # GET view
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'gestion_tic/activos/activos_asignados.html')

        # DataTables search
        res_dt = self.client.post(url, {
            'action': 'search',
            'draw': 1,
            'start': 0,
            'length': 10,
            'search[value]': ''
        })
        self.assertEqual(res_dt.status_code, 200)
        data = res_dt.json()
        self.assertEqual(data['recordsTotal'], 1)
        self.assertEqual(data['data'][0]['codigo_barra'], 'ACT-002')
        self.assertEqual(data['data'][0]['funcionario'], 'Pedro González')
