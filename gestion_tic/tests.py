from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from core.models import Establecimiento
from core.models.funcionario import Funcionario
from core.models.unidad_organizacional import UnidadOrganizacional
from gestion_tic.models import (
    Activo, TipoActivo, MovimientoActivo, TipoMovimiento,
    Accesorio, MovimientoActivoAccesorio
)
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


class EntregaRecepcionConformeTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.establecimiento = Establecimiento.objects.create(
            nombre="Hospital Base",
            alias="HB",
            is_active=True
        )
        self.establecimiento2 = Establecimiento.objects.create(
            nombre="Hospital Curanilahue",
            alias="HC",
            is_active=True
        )
        self.user = User.objects.create_user(
            username="techuser",
            password="testpassword",
            establecimiento=self.establecimiento
        )
        self.user_est2 = User.objects.create_user(
            username="otheruser",
            password="testpassword",
            establecimiento=self.establecimiento2
        )
        self.client.login(username="techuser", password="testpassword")

        # Departamentos
        self.depto1 = UnidadOrganizacional.objects.create(
            nombre="Departamento de Informática",
            establecimiento=self.establecimiento,
            es_departamento=True,
            is_active=True
        )
        self.depto2 = UnidadOrganizacional.objects.create(
            nombre="Departamento de Recursos Humanos",
            establecimiento=self.establecimiento,
            es_departamento=True,
            is_active=True
        )

        # Funcionario histórico
        self.funcionario_historico = Funcionario.objects.create(
            rut="11111111-1",
            nombres="Carlos",
            apellidos="Valdivia",
            unidad_organizacional=self.depto2,
            establecimiento=self.establecimiento,
            is_active=True
        )

        # Jefaturas TIC
        self.jefetic = JefeTic.objects.create(
            nombre="Patricio Rodríguez",
            posicion="JEFE DPTO TIC",
            establecimiento=self.establecimiento,
            is_active=True
        )

        # Tipos de Movimiento
        self.tipo_entrega = TipoMovimiento.objects.create(
            nombre="Entrega",
            requiere_recepcion=True,
            es_asignacion=True,
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.tipo_historico = TipoMovimiento.objects.create(
            nombre="Asignación Tradicional",
            requiere_recepcion=False,
            es_asignacion=True,
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.tipo_devolucion = TipoMovimiento.objects.create(
            nombre="Devolución",
            requiere_recepcion=False,
            es_asignacion=False,
            establecimiento=self.establecimiento,
            is_active=True
        )

        # Catálogo de Accesorios
        self.mouse = Accesorio.objects.create(
            nombre="Mouse Óptico USB",
            incluido_en_estacion_completa=True,
            cantidad_estacion_completa=1,
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.teclado = Accesorio.objects.create(
            nombre="Teclado Español USB",
            incluido_en_estacion_completa=True,
            cantidad_estacion_completa=1,
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.webcam = Accesorio.objects.create(
            nombre="Webcam HD 1080p",
            incluido_en_estacion_completa=False,
            cantidad_estacion_completa=1,
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.microfono = Accesorio.objects.create(
            nombre="Micrófono Condensador",
            incluido_en_estacion_completa=False,
            cantidad_estacion_completa=1,
            establecimiento=self.establecimiento,
            is_active=True
        )

        # IPs
        self.ip_test1 = Ips.objects.create(
            ip="192.168.10.50",
            asignado=False,
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.ip_test2 = Ips.objects.create(
            ip="192.168.10.51",
            asignado=False,
            establecimiento=self.establecimiento,
            is_active=True
        )

        # Activo
        self.tipo_activo = TipoActivo.objects.create(
            nombre="Desktop",
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.marca = Marca.objects.create(
            nombre="HP",
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.modelo = Modelo.objects.create(
            nombre="EliteDesk 800 G5",
            establecimiento=self.establecimiento,
            is_active=True
        )
        self.activo = Activo.objects.create(
            codigo_barra="EQ-TEST-001",
            tipo=self.tipo_activo,
            marca=self.marca,
            modelo=self.modelo,
            serie="HP-SN-9988",
            utiliza_ip=True,
            establecimiento=self.establecimiento,
            is_active=True
        )

    def test_creacion_entrega_pendiente_sin_funcionario_con_accesorios(self):
        """Etapa A: Preparación por TIC - sin funcionario receptor y con accesorios."""
        url = reverse('gestion_tic:movimientos_activo') + f"?q={self.activo.codigo_barra}"
        post_data = {
            'tipo_movimiento': self.tipo_entrega.pk,
            'jefe_firmante': self.jefetic.pk,
            'ip': self.ip_test1.pk,
            'observacion': 'Entrega de equipo nuevo a preparar',
            'accesorio_id[]': [self.mouse.pk, self.teclado.pk],
            'accesorio_cantidad[]': ['1', '1'],
            'accesorio_observacion[]': ['Mouse nuevo en caja', 'Teclado USB standard']
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

        movimiento = MovimientoActivo.objects.filter(activo=self.activo).first()
        self.assertIsNotNone(movimiento)
        self.assertFalse(movimiento.recepcionado)
        self.assertIsNone(movimiento.funcionario)
        self.assertEqual(movimiento.tipo_movimiento, self.tipo_entrega)
        self.assertEqual(movimiento.jefe_firmante, self.jefetic)
        self.assertEqual(movimiento.ip, self.ip_test1)

        # IP debe marcarse asignada
        self.ip_test1.refresh_from_db()
        self.assertTrue(self.ip_test1.asignado)

        # Verificar accesorios creados con nombre histórico
        accesorios = movimiento.accesorios.all()
        self.assertEqual(accesorios.count(), 2)
        nombres = [acc.nombre for acc in accesorios]
        self.assertIn("Mouse Óptico USB", nombres)
        self.assertIn("Teclado Español USB", nombres)

    def test_recepcion_conforme_exitosa_y_generacion_snapshot(self):
        """Etapa B: Recepción conforme con nombre y departamento válidos."""
        mov = MovimientoActivo.objects.create(
            activo=self.activo,
            tipo_movimiento=self.tipo_entrega,
            jefe_firmante=self.jefetic,
            ip=self.ip_test1,
            establecimiento=self.establecimiento,
            recepcionado=False
        )
        MovimientoActivoAccesorio.objects.create(
            movimiento=mov,
            accesorio=self.mouse,
            nombre=self.mouse.nombre,
            cantidad=1,
            establecimiento=self.establecimiento
        )

        url_recepcion = reverse('gestion_tic:recepcion_conforme', kwargs={'pk': mov.pk})

        # GET: Renderiza formulario con equipo y accesorios
        res_get = self.client.get(url_recepcion)
        self.assertEqual(res_get.status_code, 200)
        self.assertContains(res_get, "EQ-TEST-001")
        self.assertContains(res_get, "Mouse Óptico USB")
        self.assertContains(res_get, "Declaración de Conformidad")

        # POST: Confirmación
        res_post = self.client.post(url_recepcion, {
            'nombre_completo': 'María González Tapia',
            'departamento': self.depto1.pk
        })
        self.assertEqual(res_post.status_code, 302)

        mov.refresh_from_db()
        self.assertTrue(mov.recepcionado)
        self.assertEqual(mov.nombre_completo, 'María González Tapia')
        self.assertEqual(mov.departamento, 'Departamento de Informática')
        self.assertEqual(mov.unidad_organizacional, self.depto1)
        self.assertIsNotNone(mov.fecha_recepcion)
        self.assertEqual(mov.recepcionado_por, self.user)
        self.assertIsNotNone(mov.snapshot_acta)

        # Verificar contenido del snapshot
        snapshot = mov.snapshot_acta
        self.assertEqual(snapshot['nombre_completo'], 'María González Tapia')
        self.assertEqual(snapshot['departamento'], 'Departamento de Informática')
        self.assertEqual(len(snapshot['accesorios']), 1)
        self.assertEqual(snapshot['accesorios'][0]['nombre'], 'Mouse Óptico USB')

    def test_rechazo_nombre_vacio_o_espacios_en_recepcion(self):
        """Validación en servidor: rechazar nombres vacíos o solo espacios."""
        mov = MovimientoActivo.objects.create(
            activo=self.activo,
            tipo_movimiento=self.tipo_entrega,
            jefe_firmante=self.jefetic,
            establecimiento=self.establecimiento,
            recepcionado=False
        )
        url = reverse('gestion_tic:recepcion_conforme', kwargs={'pk': mov.pk})

        # Caso solo espacios
        res = self.client.post(url, {
            'nombre_completo': '    ',
            'departamento': self.depto1.pk
        })
        self.assertEqual(res.status_code, 200)
        mov.refresh_from_db()
        self.assertFalse(mov.recepcionado)

        # Caso vacío
        res2 = self.client.post(url, {
            'nombre_completo': '',
            'departamento': self.depto1.pk
        })
        self.assertEqual(res2.status_code, 200)
        mov.refresh_from_db()
        self.assertFalse(mov.recepcionado)

    def test_proteccion_contra_doble_confirmacion(self):
        """Impide confirmar nuevamente una recepción ya confirmada."""
        mov = MovimientoActivo.objects.create(
            activo=self.activo,
            tipo_movimiento=self.tipo_entrega,
            jefe_firmante=self.jefetic,
            establecimiento=self.establecimiento,
            recepcionado=True,
            nombre_completo="Receptor Original",
            departamento="Dpto Original"
        )
        url = reverse('gestion_tic:recepcion_conforme', kwargs={'pk': mov.pk})

        # GET debe advertir y redirigir
        res_get = self.client.get(url)
        self.assertEqual(res_get.status_code, 302)

        # POST debe rechazar
        res_post = self.client.post(url, {
            'nombre_completo': 'Nuevo Receptor Falso',
            'departamento': self.depto2.pk
        })
        self.assertEqual(res_post.status_code, 302)
        mov.refresh_from_db()
        self.assertEqual(mov.nombre_completo, "Receptor Original")

    def test_rechazo_recepcion_tipo_no_requerido(self):
        """Rechaza la recepción de movimientos que no la requieran."""
        mov = MovimientoActivo.objects.create(
            activo=self.activo,
            tipo_movimiento=self.tipo_historico,  # requiere_recepcion=False
            jefe_firmante=self.jefetic,
            establecimiento=self.establecimiento,
            recepcionado=False
        )
        url = reverse('gestion_tic:recepcion_conforme', kwargs={'pk': mov.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)

    def test_rechazo_confirmacion_movimiento_reemplazado(self):
        """Evita confirmar una entrega antigua reemplazada por movimientos posteriores."""
        mov1 = MovimientoActivo.objects.create(
            activo=self.activo,
            tipo_movimiento=self.tipo_entrega,
            jefe_firmante=self.jefetic,
            establecimiento=self.establecimiento,
            recepcionado=False
        )
        # Se registra un segundo movimiento posterior
        mov2 = MovimientoActivo.objects.create(
            activo=self.activo,
            tipo_movimiento=self.tipo_devolucion,
            jefe_firmante=self.jefetic,
            establecimiento=self.establecimiento,
            recepcionado=False
        )
        url = reverse('gestion_tic:recepcion_conforme', kwargs={'pk': mov1.pk})
        res = self.client.post(url, {
            'nombre_completo': 'Intento Confirmar Viejo',
            'departamento': self.depto1.pk
        })
        self.assertEqual(res.status_code, 302)
        mov1.refresh_from_db()
        self.assertFalse(mov1.recepcionado)

    def test_aislamiento_por_establecimiento(self):
        """Aislamiento multi-tenant por establecimiento."""
        mov_est1 = MovimientoActivo.objects.create(
            activo=self.activo,
            tipo_movimiento=self.tipo_entrega,
            jefe_firmante=self.jefetic,
            establecimiento=self.establecimiento,
            recepcionado=False
        )
        self.client.login(username="otheruser", password="testpassword")
        url = reverse('gestion_tic:recepcion_conforme', kwargs={'pk': mov_est1.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 404)

        url_pdf = reverse('gestion_tic:activo_acta_pdf', kwargs={'pk': mov_est1.pk})
        res_pdf = self.client.get(url_pdf)
        self.assertEqual(res_pdf.status_code, 404)

    def test_listado_activos_asignados_visibilidad(self):
        """Visibilidad en listado de activos asignados según nuevo flujo y compatibilidad."""
        # 1. Movimiento pendiente NO debe aparecer
        mov_pendiente = MovimientoActivo.objects.create(
            activo=self.activo,
            tipo_movimiento=self.tipo_entrega,
            establecimiento=self.establecimiento,
            recepcionado=False
        )
        url_asig = reverse('gestion_tic:activo_list_asignado')
        res1 = self.client.post(url_asig, {
            'action': 'search', 'draw': 1, 'start': 0, 'length': 10, 'search[value]': ''
        })
        self.assertEqual(res1.json()['recordsTotal'], 0)

        # 2. Confirmar recepción -> DEBE aparecer con nombre y depto
        mov_pendiente.recepcionado = True
        mov_pendiente.nombre_completo = "Ana Morales"
        mov_pendiente.departamento = "Departamento de Informática"
        mov_pendiente.unidad_organizacional = self.depto1
        mov_pendiente.save()

        res2 = self.client.post(url_asig, {
            'action': 'search', 'draw': 2, 'start': 0, 'length': 10, 'search[value]': ''
        })
        self.assertEqual(res2.json()['recordsTotal'], 1)
        self.assertEqual(res2.json()['data'][0]['funcionario'], 'Ana Morales')
        self.assertEqual(res2.json()['data'][0]['unidad_organizacional'], 'Departamento de Informática')

    def test_orden_historial_estable_al_confirmar_movimiento(self):
        """El orden del historial no se corrompe al actualizar updated_at de un movimiento anterior."""
        mov1 = MovimientoActivo.objects.create(
            activo=self.activo,
            tipo_movimiento=self.tipo_entrega,
            establecimiento=self.establecimiento,
            recepcionado=False
        )
        mov2 = MovimientoActivo.objects.create(
            activo=self.activo,
            tipo_movimiento=self.tipo_devolucion,
            establecimiento=self.establecimiento,
            recepcionado=False
        )
        # Confirmar mov1 posteriormente (cambia su updated_at)
        mov1.recepcionado = True
        mov1.nombre_completo = "Prueba Orden"
        mov1.save()

        # El último movimiento sigue siendo mov2
        ultimo = self.activo.movimientos.order_by('-created_at', '-id').first()
        self.assertEqual(ultimo.pk, mov2.pk)

    def test_acta_pdf_contenido_pendiente_y_confirmada(self):
        """Generación de PDF para entrega pendiente vs confirmada."""
        mov = MovimientoActivo.objects.create(
            activo=self.activo,
            tipo_movimiento=self.tipo_entrega,
            jefe_firmante=self.jefetic,
            ip=self.ip_test1,
            establecimiento=self.establecimiento,
            recepcionado=False
        )
        MovimientoActivoAccesorio.objects.create(
            movimiento=mov,
            accesorio=self.mouse,
            nombre=self.mouse.nombre,
            cantidad=1,
            establecimiento=self.establecimiento
        )

        url_pdf = reverse('gestion_tic:activo_acta_pdf', kwargs={'pk': mov.pk})

        # Acta pendiente
        res_pdf_pend = self.client.get(url_pdf)
        self.assertEqual(res_pdf_pend.status_code, 200)
        self.assertEqual(res_pdf_pend['Content-Type'], 'application/pdf')

        # Confirmar y generar acta confirmada
        mov.recepcionado = True
        mov.nombre_completo = "Receptor Confirmado"
        mov.departamento = "Departamento de Recursos Humanos"
        mov.snapshot_acta = mov.generar_snapshot_acta()
        mov.save()

        res_pdf_conf = self.client.get(url_pdf)
        self.assertEqual(res_pdf_conf.status_code, 200)
        self.assertEqual(res_pdf_conf['Content-Type'], 'application/pdf')

    def test_conservacion_historica_snapshot_acta(self):
        """Comprueba que editar los catálogos en el futuro no altera el snapshot histórico."""
        mov = MovimientoActivo.objects.create(
            activo=self.activo,
            tipo_movimiento=self.tipo_entrega,
            jefe_firmante=self.jefetic,
            establecimiento=self.establecimiento,
            recepcionado=True,
            nombre_completo="Receptor Permanente",
            departamento="Departamento de Informática"
        )
        MovimientoActivoAccesorio.objects.create(
            movimiento=mov,
            accesorio=self.mouse,
            nombre=self.mouse.nombre,
            cantidad=2,
            establecimiento=self.establecimiento
        )
        mov.snapshot_acta = mov.generar_snapshot_acta()
        mov.save()

        # Cambiar el nombre de la marca y del accesorio en la base de datos
        self.marca.nombre = "Marca Modificada Posteriormente"
        self.marca.save()
        self.mouse.nombre = "Mouse Bluetooth Modificado"
        self.mouse.save()

        mov.refresh_from_db()
        snapshot = mov.snapshot_acta
        self.assertEqual(snapshot['activo']['marca'], 'HP')
        self.assertEqual(snapshot['accesorios'][0]['nombre'], 'Mouse Óptico USB')

    def test_comportamiento_ip_asignacion_y_liberacion(self):
        """Manejo de estados de IPs entre movimientos consecutivos."""
        url = reverse('gestion_tic:movimientos_activo') + f"?q={self.activo.codigo_barra}"

        # 1. Movimiento asigna IP 1
        self.client.post(url, {
            'tipo_movimiento': self.tipo_entrega.pk,
            'jefe_firmante': self.jefetic.pk,
            'ip': self.ip_test1.pk,
            'observacion': 'Asigna IP 1'
        })
        self.ip_test1.refresh_from_db()
        self.assertTrue(self.ip_test1.asignado)

        # 2. Movimiento cambia a IP 2 (debe liberar IP 1)
        self.client.post(url, {
            'tipo_movimiento': self.tipo_entrega.pk,
            'jefe_firmante': self.jefetic.pk,
            'ip': self.ip_test2.pk,
            'observacion': 'Cambia a IP 2'
        })
        self.ip_test1.refresh_from_db()
        self.ip_test2.refresh_from_db()
        self.assertFalse(self.ip_test1.asignado)
        self.assertTrue(self.ip_test2.asignado)

        # 3. Movimiento sin IP (debe liberar IP 2)
        self.client.post(url, {
            'tipo_movimiento': self.tipo_devolucion.pk,
            'jefe_firmante': self.jefetic.pk,
            'ip': '',
            'observacion': 'Devolución sin IP'
        })
        self.ip_test2.refresh_from_db()
        self.assertFalse(self.ip_test2.asignado)

    def test_crud_catalogo_accesorios(self):
        """CRUD para mantenedor de accesorios."""
        # List
        url_list = reverse('gestion_tic:accesorio_list')
        res_list = self.client.get(url_list)
        self.assertEqual(res_list.status_code, 200)

        # Create
        url_create = reverse('gestion_tic:accesorio_create')
        res_create = self.client.post(url_create, {
            'nombre': 'Adaptador HDMI a VGA',
            'descripcion': 'Conversor de video',
            'incluido_en_estacion_completa': True,
            'cantidad_estacion_completa': 1
        })
        self.assertEqual(res_create.status_code, 302)
        nuevo_acc = Accesorio.objects.filter(nombre='Adaptador HDMI a VGA').first()
        self.assertIsNotNone(nuevo_acc)
        self.assertTrue(nuevo_acc.incluido_en_estacion_completa)

        # Update
        url_update = reverse('gestion_tic:accesorio_update', kwargs={'pk': nuevo_acc.pk})
        res_update = self.client.post(url_update, {
            'nombre': 'Adaptador HDMI a VGA V2',
            'descripcion': 'Conversor actualizado',
            'cantidad_estacion_completa': 2
        })
        self.assertEqual(res_update.status_code, 302)
        nuevo_acc.refresh_from_db()
        self.assertEqual(nuevo_acc.nombre, 'Adaptador HDMI a VGA V2')

        # Deactivate
        url_deact = reverse('gestion_tic:accesorio_deactivate', kwargs={'pk': nuevo_acc.pk})
        res_deact = self.client.post(url_deact)
        self.assertEqual(res_deact.status_code, 200)
        nuevo_acc.refresh_from_db()
        self.assertFalse(nuevo_acc.is_active)
