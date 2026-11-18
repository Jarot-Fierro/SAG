from django.test import TestCase
from django.urls import reverse

from core.models.usuarios import User
from .models import Celular, Marca, Modelo, Monitor, FuncionarioInventario


class MonitorTests(TestCase):
    def test_codigo_automatico_se_conserva_al_actualizar(self):
        marca = Marca.objects.create(nombre='Marca')
        modelo = Modelo.objects.create(nombre='Modelo', marca=marca)
        for serie in ('MON-001', 'MON-002'):
            monitor = Monitor.objects.create(
                marca=marca, modelo=modelo, numero_serie=serie,
            )
            monitor.refresh_from_db()
            self.assertEqual(monitor.codigo_inventario, f'SSA-MON-{monitor.pk}')
            monitor.observacion = 'Actualizado'
            monitor.save(update_fields=['observacion'])
            monitor.refresh_from_db()
            self.assertEqual(monitor.codigo_inventario, f'SSA-MON-{monitor.pk}')
            self.assertEqual(monitor.observacion, 'Actualizado')
            self.assertEqual(monitor.history.first().codigo_inventario, monitor.codigo_inventario)


class CelularTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password123'
        )

    def test_codigo_automatico_y_numero_telefono(self):
        marca = Marca.objects.create(nombre='Marca')
        modelo = Modelo.objects.create(nombre='Modelo', marca=marca)
        celulares = [
            Celular.objects.create(
                marca=marca, modelo=modelo, imei=imei,
                numero_telefono='+56912345678',
            )
            for imei in ('123456789012345', '123456789012346')
        ]
        for celular in celulares:
            celular.refresh_from_db()
            self.assertEqual(celular.numero_telefono, '+56912345678')

        celular = celulares[0]
        celular.numero_telefono = '+56987654321'
        celular.save(update_fields=['numero_telefono'])
        celular.refresh_from_db()
        self.assertEqual(celular.numero_telefono, '+56987654321')

    def test_celulares_list_view_and_datatable(self):
        self.client.force_login(self.user)
        marca = Marca.objects.create(nombre='Samsung')
        modelo = Modelo.objects.create(nombre='Galaxy S21', marca=marca)
        celular = Celular.objects.create(
            marca=marca, modelo=modelo, imei='123456789012345',
            numero_telefono='+56912345678',
        )

        response = self.client.get(reverse('inventario_tic:celular_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('edit_url_template', response.context)
        self.assertIn('delete_url_template', response.context)
        self.assertContains(response, 'Acciones')
        self.assertNotContains(response, '<th>Observación</th>')

        # Test datatable POST action
        post_response = self.client.post(
            reverse('inventario_tic:celular_list'),
            {'action': 'search', 'draw': 1, 'start': 0, 'length': 10}
        )
        self.assertEqual(post_response.status_code, 200)
        data = post_response.json()
        self.assertEqual(data['recordsTotal'], 1)
        self.assertNotIn('observacion', data['data'][0])

    def test_celular_eliminar(self):
        self.client.force_login(self.user)
        marca = Marca.objects.create(nombre='Samsung')
        modelo = Modelo.objects.create(nombre='Galaxy S21', marca=marca)
        celular = Celular.objects.create(
            marca=marca, modelo=modelo, imei='123456789012345',
            numero_telefono='+56912345678',
        )

        response = self.client.post(
            reverse('inventario_tic:celular_eliminar', kwargs={'pk': celular.pk}),
            {'id': celular.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('success'))
        celular.refresh_from_db()
        self.assertFalse(celular.is_active)


class CelularActaTests(TestCase):
    def setUp(self):
        from .models.mantenedores import Establecimiento

        self.user = User.objects.create_superuser(username='acta_admin', password='test123')
        self.client.force_login(self.user)
        self.destino = Establecimiento.objects.create(nombre='Destino celular')
        self.celular = Celular.objects.create(
            imei='123456789012349', responsable=FuncionarioInventario.objects.create(nombre='Persona receptora'),
            establecimiento_mantenedor=self.destino,
        )
        self.url = reverse('inventario_tic:generar_acta_celulares', kwargs={'pk': self.celular.pk})

    def test_pdf_con_datos_opcionales_ausentes(self):
        from unittest.mock import patch

        with patch('inventario_tic.views.pdfs.HTML') as html:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('acta_celular_123456789012349.pdf', response['Content-Disposition'])
        contenido = html.call_args.kwargs['string']
        for texto in ('123456789012349', 'Persona receptora', 'Destino Celular', '<td>-</td>'):
            self.assertIn(texto, contenido)
        html.return_value.write_pdf.assert_called_once()

    def test_disponibilidad_y_validacion(self):
        from unittest.mock import patch

        for responsable, destino, disponible in (
            ('Persona', self.destino, True),
            (None, self.destino, False),
            ('', self.destino, False),
            ('   ', self.destino, False),
            ('Persona', None, False),
        ):
            with self.subTest(responsable=responsable, destino=destino):
                self.celular.responsable = FuncionarioInventario.objects.create(nombre=responsable) if responsable else None
                self.celular.establecimiento_mantenedor = destino
                self.celular.save()
                response = self.client.post(reverse('inventario_tic:celular_list'), {'action': 'search'})
                self.assertEqual(response.json()['data'][0]['puede_generar_acta'], disponible)
                with patch('inventario_tic.views.pdfs.HTML') as html:
                    response = self.client.get(self.url)
                    self.assertEqual(response.status_code, 200 if disponible else 400)
                    if not disponible:
                        html.assert_not_called()

    def test_nombre_establecimiento_vacio(self):
        self.destino.nombre = '   '
        self.destino.save()
        self.assertEqual(self.client.get(self.url).status_code, 400)

    def test_inactivo_inexistente_y_anonimo(self):
        self.celular.is_active = False
        self.celular.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        url = reverse('inventario_tic:generar_acta_celulares', kwargs={'pk': 999999})
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_restriccion_establecimiento(self):
        from core.models.establecimientos import Establecimiento

        origen = Establecimiento.objects.create(nombre='Origen')
        otro = Establecimiento.objects.create(nombre='Otro')
        self.user.is_superuser = False
        self.user.establecimiento = origen
        self.user.save()
        self.celular.establecimiento = otro
        self.celular.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.celular.establecimiento = origen
        self.celular.save()
        from unittest.mock import patch
        with patch('inventario_tic.views.pdfs.HTML'):
            self.assertEqual(self.client.get(self.url).status_code, 200)
        self.user.establecimiento = None
        self.user.save()
        self.celular.establecimiento = None
        self.celular.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)


class ImpresoraActaTests(TestCase):
    def setUp(self):
        from core.models.establecimientos import Establecimiento
        from core.models.unidad_organizacional import UnidadOrganizacional
        from .models.impresoras import Impresora

        self.user = User.objects.create_superuser(username='impresora_admin', password='test123')
        self.client.force_login(self.user)
        self.establecimiento = Establecimiento.objects.create(nombre='Servicio de prueba')
        self.departamento = UnidadOrganizacional.objects.create(
            nombre='Departamento de prueba', establecimiento=self.establecimiento,
        )
        marca = Marca.objects.create(nombre='Marca impresora')
        modelo = Modelo.objects.create(nombre='Modelo impresora', marca=marca)
        self.impresora = Impresora.objects.create(
            numero_serie='IMP-001', hh='HH-01', marca=marca, modelo=modelo,
            establecimiento=self.establecimiento, departamento=self.departamento,
        )
        self.url = reverse('inventario_tic:generar_acta_impresoras', kwargs={'pk': self.impresora.pk})

    def test_pdf_y_listado(self):
        from unittest.mock import patch

        with patch('inventario_tic.views.pdfs.HTML') as html:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('acta_impresora_IMP-001.pdf', response['Content-Disposition'])
        contenido = html.call_args.kwargs['string']
        for texto in ('IMP-001', 'HH-01', 'Departamento de prueba', 'logo_ssa.png'):
            self.assertIn(texto, contenido)
        html.return_value.write_pdf.assert_called_once()
        listado = self.client.get(reverse('inventario_tic:impresora_list'))
        self.assertContains(listado, 'data-url-acta=')
        response = self.client.post(reverse('inventario_tic:impresora_list'), {'action': 'search'})
        self.assertTrue(response.json()['data'][0]['puede_generar_acta'])

    def test_datos_faltantes(self):
        self.impresora.establecimiento = None
        self.impresora.save()
        self.assertEqual(self.client.get(self.url).status_code, 400)
        response = self.client.post(reverse('inventario_tic:impresora_list'), {'action': 'search'})
        self.assertFalse(response.json()['data'][0]['puede_generar_acta'])
        self.impresora.establecimiento = self.establecimiento
        self.impresora.save()
        self.departamento.nombre = '   '
        self.departamento.save()
        self.assertEqual(self.client.get(self.url).status_code, 400)

    def test_acceso(self):
        from core.models.establecimientos import Establecimiento
        from unittest.mock import patch

        self.user.is_superuser = False
        self.user.establecimiento = Establecimiento.objects.create(nombre='Otro servicio')
        self.user.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.user.establecimiento = self.establecimiento
        self.user.save()
        with patch('inventario_tic.views.pdfs.HTML'):
            self.assertEqual(self.client.get(self.url).status_code, 200)
        self.user.establecimiento = None
        self.user.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.user.is_superuser = True
        self.user.save()
        self.impresora.is_active = False
        self.impresora.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)


class MonitorViewsTests(TestCase):
    def setUp(self):
        from core.models.establecimientos import Establecimiento
        self.establecimiento = Establecimiento.objects.create(nombre='Servicio monitores')
        self.user = User.objects.create_superuser(username='monitor_admin', password='test123', establecimiento=self.establecimiento)
        self.client.force_login(self.user)
        self.marca = Marca.objects.create(nombre='Marca monitor')
        self.modelo = Modelo.objects.create(nombre='Modelo monitor', marca=self.marca)
        self.data = {'numero_serie': 'mon-001', 'marca': self.marca.pk, 'modelo': self.modelo.pk,
                     'pulgadas': '24.0', 'resolucion': '1920 x 1080', 'frecuencia_hz': '60', 'tiene_hdmi': 'on'}

    def test_crear_listar_editar_desactivar(self):
        url = reverse('inventario_tic:monitor_create')
        self.assertContains(self.client.get(url), 'monitores-modelos')
        self.assertEqual(self.client.post(url, self.data).status_code, 302)
        monitor = Monitor.objects.get()
        codigo = monitor.codigo_inventario
        self.assertEqual(monitor.establecimiento, self.establecimiento)
        self.assertTrue(monitor.tiene_hdmi)
        listado = reverse('inventario_tic:monitor_list')
        self.assertContains(self.client.get(listado), 'monitoresTable')
        result = self.client.post(listado, {'action':'search', 'search[value]':'1920'}).json()
        self.assertEqual(result['recordsFiltered'], 1)
        self.assertEqual(result['data'][0]['codigo_inventario'], codigo)
        self.assertNotIn('imei', result['data'][0])
        editar = reverse('inventario_tic:monitor_update', kwargs={'pk':monitor.pk})
        self.assertContains(self.client.get(editar), codigo)
        self.assertEqual(self.client.post(editar, {**self.data, 'resolucion':'2560 x 1440'}).status_code, 302)
        monitor.refresh_from_db()
        self.assertEqual(monitor.codigo_inventario, codigo)
        self.assertEqual(monitor.resolucion, '2560 x 1440')
        eliminar = reverse('inventario_tic:monitor_eliminar', kwargs={'pk':monitor.pk})
        self.assertEqual(self.client.get(eliminar).status_code, 405)
        self.assertTrue(self.client.post(eliminar).json()['success'])
        monitor.refresh_from_db()
        self.assertFalse(monitor.is_active)
        self.assertEqual(self.client.post(listado, {'action':'search'}).json()['recordsTotal'], 0)

    def test_validacion_formulario(self):
        from .forms.monitores import FormMonitor
        otra_marca = Marca.objects.create(nombre='Otra marca')
        form = FormMonitor(data={**self.data, 'marca':otra_marca.pk})
        self.assertFalse(form.is_valid())
        self.assertIn('modelo', form.errors)
        form = FormMonitor(data={**self.data, 'pulgadas':'0', 'frecuencia_hz':'0'})
        self.assertFalse(form.is_valid())
        self.assertIn('pulgadas', form.errors)
        self.assertIn('frecuencia_hz', form.errors)
        self.assertNotIn('codigo_inventario', form.fields)

    def test_aislamiento_y_autenticacion(self):
        monitor = Monitor.objects.create(numero_serie='AJENO', marca=self.marca, modelo=self.modelo)
        self.user.is_superuser = False
        self.user.save()
        editar = reverse('inventario_tic:monitor_update', kwargs={'pk':monitor.pk})
        eliminar = reverse('inventario_tic:monitor_eliminar', kwargs={'pk':monitor.pk})
        self.assertEqual(self.client.get(editar).status_code, 404)
        self.assertEqual(self.client.post(eliminar).status_code, 404)
        self.user.establecimiento = None
        self.user.save()
        self.assertEqual(self.client.get(editar).status_code, 404)
        self.assertEqual(self.client.post(eliminar).status_code, 404)
        listado = reverse('inventario_tic:monitor_list')
        self.assertEqual(self.client.post(listado, {'action':'search'}).json()['recordsTotal'], 0)
        self.client.logout()
        self.assertEqual(self.client.get(listado).status_code, 302)


class CelularRecepcionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='recepcion_admin', password='test123')
        self.client.force_login(self.user)
        self.celular = Celular.objects.create(imei='123456789012348', numero_telefono='+56912345678')
        self.url = reverse('inventario_tic:celular_recepcion_update', kwargs={'pk':self.celular.pk})

    def test_formularios_separados_y_guardado(self):
        from .forms.celulares import FormCelular, FormRecepcionCelular
        from .models.mantenedores import Establecimiento, JefeTic
        self.assertNotIn('responsable', FormCelular().fields)
        self.assertEqual(set(FormRecepcionCelular().fields), {'responsable', 'establecimiento_mantenedor', 'jefe_entrega'})
        destino = Establecimiento.objects.create(nombre='Destino')
        jefe = JefeTic.objects.create(nombre='Jefe', posicion='TIC')
        persona = FuncionarioInventario.objects.create(nombre='Persona')
        response = self.client.get(self.url)
        self.assertContains(response, 'funcionarioModal')
        self.assertContains(response, 'celulares_funcionario_modal.js')
        self.assertNotContains(response, 'name="imei"')
        self.assertNotContains(response, 'celulares-modelos')
        response = self.client.post(self.url, {'establecimiento_mantenedor':destino.pk, 'responsable':persona.pk, 'jefe_entrega':jefe.pk, 'imei':'000000000000000'})
        self.assertRedirects(response, reverse('inventario_tic:celular_list'))
        self.celular.refresh_from_db()
        self.assertEqual(self.celular.imei, '123456789012348')
        self.assertEqual(self.celular.numero_telefono, '+56912345678')
        self.assertEqual(self.celular.responsable, persona)
        self.assertEqual(self.celular.establecimiento_mantenedor, destino)
        self.assertEqual(self.celular.updated_by, self.user)
        self.assertEqual(Celular.objects.count(), 1)
        self.assertContains(self.client.get(reverse('inventario_tic:celular_list')), 'data-url-recepcion=')
        self.assertEqual(self.client.get(reverse('inventario_tic:celular_create')).status_code, 200)
        self.assertEqual(self.client.get(reverse('inventario_tic:celular_update', kwargs={'pk':self.celular.pk})).status_code, 200)

    def test_acceso_y_datos_invalidos(self):
        response = self.client.post(self.url, {'establecimiento_mantenedor':999999, 'responsable':'Persona'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('establecimiento_mantenedor', response.context['form'].errors)
        self.user.is_superuser = False
        self.user.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url, {}).status_code, 404)
        self.user.is_superuser = True
        self.user.save()
        self.celular.is_active = False
        self.celular.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)


class CelularDevolucionTests(TestCase):
    def setUp(self):
        from .models.mantenedores import Establecimiento, JefeTic
        from core.models.establecimientos import Establecimiento as EstablecimientoCore
        self.user = User.objects.create_superuser(username='devolucion_admin', password='test123')
        self.client.force_login(self.user)
        self.origen = EstablecimientoCore.objects.create(nombre='TIC')
        destino = Establecimiento.objects.create(nombre='Destino')
        jefe = JefeTic.objects.create(nombre='Jefe', posicion='TIC')
        self.celular = Celular.objects.create(imei='123456789012347', asignado=True, responsable=FuncionarioInventario.objects.create(nombre='Persona'),
            establecimiento=self.origen, establecimiento_mantenedor=destino, jefe_entrega=jefe)
        self.url = reverse('inventario_tic:celular_devolucion', kwargs={'pk':self.celular.pk})

    def test_devolucion_y_listado(self):
        listado = reverse('inventario_tic:celular_list')
        self.assertTrue(self.client.post(listado, {'action':'search'}).json()['data'][0]['asignado'])
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertTrue(self.client.post(self.url).json()['success'])
        self.celular.refresh_from_db()
        self.assertFalse(self.celular.asignado)
        self.assertIsNone(self.celular.responsable)
        self.assertIsNone(self.celular.establecimiento_mantenedor)
        self.assertIsNone(self.celular.jefe_entrega)
        self.assertEqual(self.celular.establecimiento, self.origen)
        self.assertTrue(self.celular.is_active)
        self.assertEqual(self.celular.updated_by, self.user)
        data = self.client.post(listado, {'action':'search'}).json()['data'][0]
        self.assertFalse(data['asignado'])
        self.assertFalse(data['puede_generar_acta'])
        self.assertEqual(self.client.post(self.url).status_code, 400)

    def test_permisos(self):
        self.user.is_superuser = False
        self.user.save()
        self.assertEqual(self.client.post(self.url).status_code, 404)
        self.celular.refresh_from_db()
        self.assertTrue(self.celular.asignado)
        self.user.establecimiento = self.origen
        self.user.save()
        self.assertEqual(self.client.post(self.url).status_code, 200)
        self.client.logout()
        self.assertEqual(self.client.post(self.url).status_code, 302)


class MonitorRecepcionDevolucionTests(TestCase):
    def setUp(self):
        MonitorViewsTests.setUp(self)
        self.monitor = Monitor.objects.create(numero_serie='MON-FLUJO', marca=self.marca,
            modelo=self.modelo, establecimiento=self.establecimiento, pulgadas='24.0')
        self.recepcion = reverse('inventario_tic:monitor_recepcion_update', kwargs={'pk':self.monitor.pk})
        self.devolucion = reverse('inventario_tic:monitor_devolucion', kwargs={'pk':self.monitor.pk})

    def test_ciclo_completo_y_separacion(self):
        from .forms.monitores import FormMonitor, FormRecepcionMonitor
        from .models.mantenedores import Establecimiento, JefeTic
        self.assertNotIn('responsable', FormMonitor().fields)
        self.assertEqual(set(FormRecepcionMonitor().fields), {'responsable', 'establecimiento_mantenedor', 'jefe_entrega'})
        destino = Establecimiento.objects.create(nombre='Destino monitor')
        jefe = JefeTic.objects.create(nombre='Jefe monitor', posicion='TIC')
        response = self.client.get(self.recepcion)
        self.assertContains(response, 'monitores_form.js')
        self.assertNotContains(response, 'name="numero_serie"')
        codigo = self.monitor.codigo_inventario
        data = {'responsable':'Persona', 'establecimiento_mantenedor':destino.pk, 'jefe_entrega':jefe.pk,
                'numero_serie':'CAMBIO NO PERMITIDO'}
        self.assertRedirects(self.client.post(self.recepcion, data), reverse('inventario_tic:monitor_list'))
        self.monitor.refresh_from_db()
        self.assertTrue(self.monitor.asignado)
        self.assertEqual(self.monitor.responsable, 'Persona')
        self.assertEqual(self.monitor.numero_serie, 'MON-FLUJO')
        self.assertEqual(self.monitor.codigo_inventario, codigo)
        listado = reverse('inventario_tic:monitor_list')
        self.assertContains(self.client.get(listado), 'data-url-devolucion=')
        row = self.client.post(listado, {'action':'search'}).json()['data'][0]
        self.assertTrue(row['asignado'])
        self.assertEqual(row['responsable'], 'Persona')
        self.assertEqual(self.client.get(self.devolucion).status_code, 405)
        self.assertTrue(self.client.post(self.devolucion).json()['success'])
        self.monitor.refresh_from_db()
        self.assertFalse(self.monitor.asignado)
        self.assertIsNone(self.monitor.responsable)
        self.assertIsNone(self.monitor.establecimiento_mantenedor)
        self.assertIsNone(self.monitor.jefe_entrega)
        self.assertEqual(self.monitor.establecimiento, self.establecimiento)
        self.assertEqual(self.monitor.codigo_inventario, codigo)
        self.assertEqual(self.monitor.updated_by, self.user)
        self.assertEqual(self.client.post(self.devolucion).status_code, 400)

    def test_permisos_e_invalido(self):
        response = self.client.post(self.recepcion, {'establecimiento_mantenedor':999999})
        self.assertEqual(response.status_code, 200)
        self.monitor.refresh_from_db()
        self.assertFalse(self.monitor.asignado)
        self.user.is_superuser = False
        self.user.establecimiento = None
        self.user.save()
        self.assertEqual(self.client.get(self.recepcion).status_code, 404)
        self.assertEqual(self.client.post(self.devolucion).status_code, 404)
        self.user.is_superuser = True
        self.user.save()
        self.monitor.is_active = False
        self.monitor.save()
        self.assertEqual(self.client.get(self.recepcion).status_code, 404)
        self.assertEqual(self.client.post(self.devolucion).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(self.recepcion).status_code, 302)


class MonitorActaTests(TestCase):
    def setUp(self):
        MonitorRecepcionDevolucionTests.setUp(self)
        from .models.mantenedores import Establecimiento
        self.destino = Establecimiento.objects.create(nombre='Destino monitor')
        self.monitor.establecimiento_mantenedor = self.destino
        self.monitor.responsable = 'Persona receptora'
        self.monitor.save()
        self.url = reverse('inventario_tic:generar_acta_monitores', kwargs={'pk':self.monitor.pk})

    def test_pdf_con_logo_y_datos(self):
        from unittest.mock import patch
        with patch('inventario_tic.views.pdfs.HTML') as html:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn(self.monitor.codigo_inventario, response['Content-Disposition'])
        contenido = html.call_args.kwargs['string']
        for texto in ('MON-FLUJO', self.monitor.codigo_inventario, 'Persona receptora', 'Destino Monitor', 'data:image/png;base64,'):
            self.assertIn(texto, contenido)
        self.assertIn('<th>HDMI</th><td>No</td>', contenido)
        html.return_value.write_pdf.assert_called_once()

    def test_requisitos_y_listado(self):
        from unittest.mock import patch
        for responsable, destino, disponible in (
            ('Persona', self.destino, True), (None, self.destino, False),
            ('', self.destino, False), ('   ', self.destino, False), ('Persona', None, False),
        ):
            with self.subTest(responsable=responsable, destino=destino):
                self.monitor.responsable = responsable
                self.monitor.establecimiento_mantenedor = destino
                self.monitor.save()
                data = self.client.post(reverse('inventario_tic:monitor_list'), {'action':'search'}).json()['data'][0]
                self.assertEqual(data['puede_generar_acta'], disponible)
                with patch('inventario_tic.views.pdfs.HTML') as html:
                    self.assertEqual(self.client.get(self.url).status_code, 200 if disponible else 400)
                    if not disponible:
                        html.assert_not_called()

    def test_permisos(self):
        self.user.is_superuser = False
        self.user.establecimiento = None
        self.user.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.user.is_superuser = True
        self.user.save()
        self.monitor.is_active = False
        self.monitor.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)


class FuncionarioInventarioTests(TestCase):
    def setUp(self):
        from core.models.establecimientos import Establecimiento
        self.establecimiento = Establecimiento.objects.create(nombre='Servicio funcionarios')
        self.otro = Establecimiento.objects.create(nombre='Otro servicio funcionarios')
        self.user = User.objects.create_user(username='funcionario_editor', password='test123', establecimiento=self.establecimiento)
        self.client.force_login(self.user)
        self.modal = reverse('inventario_tic:funcionario_create_modal')

    def test_modal_y_recepcion(self):
        from .models.mantenedores import Establecimiento, JefeTic
        celular = Celular.objects.create(imei='555555555555555', establecimiento=self.establecimiento)
        jefe = JefeTic.objects.create(nombre='Jefe', posicion='TIC')
        destino = Establecimiento.objects.create(nombre='Destino')
        url = reverse('inventario_tic:celular_recepcion_update', kwargs={'pk':celular.pk})
        self.assertContains(self.client.get(url), 'funcionarioModalForm')
        response = self.client.post(self.modal, {'nombre':'  Ana   Perez  '})
        self.assertEqual(response.status_code, 201)
        persona = FuncionarioInventario.objects.get(pk=response.json()['id'])
        self.assertEqual(persona.nombre, 'Ana Perez')
        self.assertEqual(persona.establecimiento, self.establecimiento)
        self.assertEqual(persona.created_by, self.user)
        self.assertFalse(response.json()['coincidencias'])
        response = self.client.post(url, {'responsable':persona.pk, 'jefe_entrega':jefe.pk, 'establecimiento_mantenedor':destino.pk})
        self.assertEqual(response.status_code, 302)
        celular.refresh_from_db()
        self.assertTrue(celular.asignado)
        self.assertEqual(celular.responsable, persona)
        listado = self.client.post(reverse('inventario_tic:celular_list'), {'action':'search','search[value]':'Ana'}).json()
        self.assertEqual(listado['recordsFiltered'], 1)
        self.assertEqual(listado['data'][0]['responsable'], 'Ana Perez')
        self.assertTrue(listado['data'][0]['puede_generar_acta'])
        self.assertTrue(self.client.post(reverse('inventario_tic:celular_devolucion',kwargs={'pk':celular.pk})).json()['success'])
        self.assertTrue(FuncionarioInventario.objects.filter(pk=persona.pk).exists())

    def test_crud_y_duplicados(self):
        lista = reverse('inventario_tic:funcionario_list')
        crear = reverse('inventario_tic:funcionario_create')
        self.assertContains(self.client.get(lista), 'funcionarios_datatable.js')
        self.assertContains(self.client.get(crear), 'funcionarios_form.js')
        self.assertEqual(self.client.post(crear, {'nombre':'Persona'}).status_code, 302)
        persona = FuncionarioInventario.objects.get()
        editar = reverse('inventario_tic:funcionario_update', kwargs={'pk':persona.pk})
        self.assertEqual(self.client.post(editar, {'nombre':'Persona editada'}).status_code, 302)
        persona.refresh_from_db()
        self.assertEqual(persona.updated_by, self.user)
        duplicado = self.client.post(self.modal, {'nombre':'persona editada'})
        self.assertEqual(duplicado.status_code, 201)
        self.assertTrue(duplicado.json()['coincidencias'])
        data = self.client.post(lista, {'action':'search','search[value]':'editada'}).json()
        self.assertEqual(data['recordsFiltered'], 2)
        desactivar = reverse('inventario_tic:funcionario_deactivate', kwargs={'pk':persona.pk})
        self.assertEqual(self.client.get(desactivar).status_code, 405)
        self.assertTrue(self.client.post(desactivar).json()['success'])
        persona.refresh_from_db()
        self.assertFalse(persona.is_active)

    def test_validacion_y_aislamiento(self):
        from .forms.celulares import FormRecepcionCelular
        persona = FuncionarioInventario.objects.create(nombre='Ajeno', establecimiento=self.otro)
        inactivo = FuncionarioInventario.objects.create(nombre='Inactivo', establecimiento=self.establecimiento, is_active=False)
        for pk in (persona.pk, inactivo.pk, 999999):
            from django.test import RequestFactory
            request = RequestFactory().get('/')
            request.user = self.user
            form = FormRecepcionCelular(data={'responsable':pk}, request=request)
            self.assertFalse(form.is_valid())
            self.assertIn('responsable', form.errors)
        for nombre in ('', '   ', 'x'*256):
            self.assertEqual(self.client.post(self.modal, {'nombre':nombre}).status_code, 400)
        editar = reverse('inventario_tic:funcionario_update', kwargs={'pk':persona.pk})
        self.assertEqual(self.client.get(editar).status_code, 404)
        self.assertEqual(self.client.post(reverse('inventario_tic:funcionario_deactivate', kwargs={'pk':persona.pk})).status_code, 404)
        self.assertEqual(self.client.post(reverse('inventario_tic:funcionario_list'), {'action':'search'}).json()['recordsTotal'], 0)
        self.user.establecimiento = None
        self.user.save()
        self.assertEqual(self.client.post(self.modal, {'nombre':'Sin establecimiento'}).status_code, 400)
        self.client.logout()
        self.assertEqual(self.client.post(self.modal, {'nombre':'Anonimo'}).status_code, 302)

    def test_csrf_modal(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(self.modal, {'nombre':'Sin CSRF'}).status_code, 403)
