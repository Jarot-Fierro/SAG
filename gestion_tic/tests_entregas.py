from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError, PermissionDenied
from django.test import TestCase
from django.urls import reverse

from core.models import Establecimiento
from core.models.funcionario import Funcionario
from core.models.unidad_organizacional import UnidadOrganizacional
from gestion_tic.entregas import confirmar_entrega, recepcionar_entrega
from gestion_tic.models import (EntregaActivos, DetalleEntrega, Activo, TipoActivo,
                                TipoMovimiento, JefeTic, Ips, Accesorio, MovimientoActivo)


class EntregasTestCase(TestCase):
    def setUp(self):
        self.est = Establecimiento.objects.create(nombre='Hospital', alias='H')
        self.otro_est = Establecimiento.objects.create(nombre='Otro', alias='O')
        self.unidad = UnidadOrganizacional.objects.create(nombre='Unidad', establecimiento=self.est)
        self.funcionario = Funcionario.objects.create(nombre='Persona receptora',
                                                      establecimiento=self.est, unidad_organizacional=self.unidad)
        User = get_user_model()
        self.tecnico = User.objects.create_user(username='tecnico', establecimiento=self.est)
        self.tecnico.user_permissions.add(Permission.objects.get(
            content_type__app_label='gestion_tic', codename='add_movimientoactivo'))
        self.receptor = User.objects.create_user(username='receptor', establecimiento=self.est,
                                                 funcionario=self.funcionario)
        self.otro = User.objects.create_user(username='otro', establecimiento=self.est)
        self.tipo = TipoActivo.objects.create(nombre='Equipo', establecimiento=self.est)
        self.tipo_mov = TipoMovimiento.objects.create(nombre='Entrega', requiere_recepcion=True,
                                                      es_asignacion=True, establecimiento=self.est)
        self.jefe = JefeTic.objects.create(nombre='Jefatura', posicion='Jefe', establecimiento=self.est)
        self.a = Activo.objects.create(codigo_barra='A', tipo=self.tipo, establecimiento=self.est,
                                       utiliza_ip=True)
        self.b = Activo.objects.create(codigo_barra='B', tipo=self.tipo, establecimiento=self.est)
        self.ip = Ips.objects.create(ip='10.0.0.1', establecimiento=self.est)
        self.acc = Accesorio.objects.create(nombre='Mouse', establecimiento=self.est)
        self.entrega = EntregaActivos.objects.create(funcionario=self.funcionario,
                                                     tipo_movimiento=self.tipo_mov, jefe_firmante=self.jefe,
                                                     establecimiento=self.est,
                                                     created_by=self.tecnico)
        self.da = DetalleEntrega.objects.create(entrega=self.entrega, activo=self.a, ip=self.ip,
                                                accesorios=[{'id': self.acc.pk, 'cantidad': 2, 'observacion': 'USB'}])
        DetalleEntrega.objects.create(entrega=self.entrega, activo=self.b)

    def url(self, name='entrega_detalle', **kwargs):
        return reverse('gestion_tic:' + name, kwargs=kwargs or {'pk': self.entrega.pk})

    def test_entrega_recepcion_e_historial_con_snapshot_inmutable(self):
        confirmar_entrega(self.entrega.pk, self.tecnico)
        self.assertEqual(self.entrega.movimientos.count(), 2)
        self.assertFalse(self.entrega.movimientos.filter(recepcionado=True).exists())
        self.ip.refresh_from_db()
        self.assertTrue(self.ip.asignado)
        self.a.codigo_barra = 'CAMBIADO'
        self.a.save()
        self.acc.nombre = 'Nuevo nombre'
        self.acc.save()
        entrega = recepcionar_entrega(self.entrega.pk, self.receptor)
        self.assertEqual(entrega.estado, 'recepcionada')
        self.assertEqual(entrega.movimientos.filter(recepcionado=True).count(), 2)
        self.assertEqual(entrega.snapshot_acta['activos'][0]['activo']['codigo_barra'], 'A')
        self.assertEqual(entrega.snapshot_acta['activos'][0]['accesorios'][0]['nombre'], 'Mouse')
        for m in entrega.movimientos.all():
            self.assertEqual(m.recepcionado_por, self.receptor)
            self.assertEqual(m.fecha_recepcion, entrega.fecha_recepcion)
            self.assertIsNotNone(m.snapshot_acta)
        with self.assertRaises(ValidationError):
            recepcionar_entrega(entrega.pk, self.receptor)
        with self.assertRaises(ValidationError):
            confirmar_entrega(entrega.pk, self.tecnico)

    def test_fallo_revierte_todos_los_movimientos_e_ips(self):
        self.b.de_baja = True
        self.b.save()
        with self.assertRaises(ValidationError):
            confirmar_entrega(self.entrega.pk, self.tecnico)
        self.assertEqual(self.entrega.movimientos.count(), 0)
        self.ip.refresh_from_db()
        self.assertFalse(self.ip.asignado)
        self.entrega.refresh_from_db()
        self.assertEqual(self.entrega.estado, 'borrador')

    def test_accesorio_invalido_revierte_movimientos_ya_creados(self):
        self.acc.is_active = False
        self.acc.save()
        with self.assertRaises(ValidationError):
            confirmar_entrega(self.entrega.pk, self.tecnico)
        self.assertFalse(self.entrega.movimientos.exists())
        self.ip.refresh_from_db()
        self.assertFalse(self.ip.asignado)

    def test_ip_ocupada_y_repetida(self):
        self.ip.asignado = True
        self.ip.save()
        with self.assertRaises(ValidationError):
            confirmar_entrega(self.entrega.pk, self.tecnico)
        self.ip.asignado = False
        self.ip.save()
        self.b.utiliza_ip = True
        self.b.save()
        DetalleEntrega.objects.filter(activo=self.b).update(ip=self.ip)
        with self.assertRaises(ValidationError):
            confirmar_entrega(self.entrega.pk, self.tecnico)
        self.assertFalse(self.entrega.movimientos.exists())

    def test_usuario_sin_permiso_y_sin_recepcion_parcial(self):
        confirmar_entrega(self.entrega.pk, self.tecnico)
        with self.assertRaises(PermissionDenied):
            recepcionar_entrega(self.entrega.pk, self.otro)
        # Simular un movimiento posterior externo: se rechaza el conjunto.
        MovimientoActivo.objects.create(activo=self.b, tipo_movimiento=self.tipo_mov,
                                        establecimiento=self.est)
        with self.assertRaises(ValidationError):
            recepcionar_entrega(self.entrega.pk, self.receptor)
        self.assertFalse(self.entrega.movimientos.filter(recepcionado=True).exists())

    def test_conflicto_entre_carritos_y_bloqueo_del_flujo_individual(self):
        otra = EntregaActivos.objects.create(funcionario=self.funcionario,
                                             tipo_movimiento=self.tipo_mov, jefe_firmante=self.jefe,
                                             establecimiento=self.est)
        DetalleEntrega.objects.create(entrega=otra, activo=self.a)
        confirmar_entrega(self.entrega.pk, self.tecnico)
        with self.assertRaises(ValidationError):
            confirmar_entrega(otra.pk, self.tecnico)
        from gestion_tic.views.movimientos_activo import _guardar_movimiento_con_accesorios
        from django.http import QueryDict
        with self.assertRaises(ValidationError):
            _guardar_movimiento_con_accesorios(None, self.a, self.est, self.tecnico, QueryDict())

    def test_permisos_aislamiento_y_paginas(self):
        self.client.force_login(self.receptor)
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.client.force_login(self.otro)
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.assertEqual(self.client.get(reverse('gestion_tic:entrega_nueva')).status_code, 403)
        self.client.force_login(self.tecnico)
        for url in [self.url(), self.url('entrega_agregar'), reverse('gestion_tic:entrega_nueva'),
                    reverse('gestion_tic:entrega_list')]:
            self.assertEqual(self.client.get(url).status_code, 200)
        self.tecnico.establecimiento = self.otro_est
        self.tecnico.save()
        self.assertEqual(self.client.get(self.url()).status_code, 404)

    def test_carrito_agregar_editar_quitar_y_duplicado(self):
        self.client.force_login(self.tecnico)
        payload = {'codigo': 'B', 'observacion': 'Detalle', 'ip': '',
                   'form-TOTAL_FORMS': 1, 'form-INITIAL_FORMS': 0, 'form-0-cantidad': 1}
        response = self.client.post(self.url('entrega_agregar'), payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ya est', status_code=200)
        item = self.entrega.detalles.get(activo=self.b)
        self.client.post(self.url(), {'accion': 'quitar', 'detalle': item.pk})
        self.assertFalse(self.entrega.detalles.filter(pk=item.pk).exists())
        response = self.client.post(self.url('entrega_agregar'), payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.entrega.detalles.get(activo=self.b).observacion, 'Detalle')

    def test_vista_recepcion_total_y_pdf(self):
        self.client.force_login(self.tecnico)
        self.assertEqual(self.client.post(self.url(), {'accion': 'confirmar', 'funcionario': self.funcionario.pk,
                                                       'tipo_movimiento': self.tipo_mov.pk,
                                                       'jefe_firmante': self.jefe.pk,
                                                       'observacion': 'Conjunto'}).status_code, 302)
        self.client.force_login(self.receptor)
        self.assertEqual(self.client.get(self.url()).status_code, 200)
        self.client.post(self.url(), {'accion': 'recepcionar'})
        self.entrega.refresh_from_db()
        self.assertEqual(self.entrega.estado, 'pendiente')
        self.client.post(self.url(), {'accion': 'recepcionar', 'conforme': 'si'})
        self.entrega.refresh_from_db()
        self.assertEqual(self.entrega.estado, 'recepcionada')
        response = self.client.get(self.url('entrega_acta'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF'))
        mov = self.entrega.movimientos.first()
        self.assertRedirects(self.client.get(reverse('gestion_tic:recepcion_conforme', kwargs={'pk': mov.pk})),
                             self.url(), fetch_redirect_response=False)
        self.assertRedirects(self.client.get(reverse('gestion_tic:activo_acta_pdf', kwargs={'pk': mov.pk})),
                             self.url('entrega_acta'), fetch_redirect_response=False)

    def test_compatibilidad_con_movimientos_anteriores(self):
        anterior = MovimientoActivo.objects.create(activo=self.a, tipo_movimiento=self.tipo_mov,
                                                   establecimiento=self.est, funcionario=self.funcionario, ip=self.ip)
        self.ip.asignado = True
        self.ip.save()
        confirmar_entrega(self.entrega.pk, self.tecnico)
        anterior.refresh_from_db()
        self.assertIsNone(anterior.entrega_id)
        self.assertEqual(self.a.movimientos.count(), 2)
        recepcionar_entrega(self.entrega.pk, self.receptor)
        # Tras recibir se permite mover un equipo individualmente.
        from gestion_tic.entregas import validar_disponibilidad
        self.assertEqual(validar_disponibilidad(self.a).entrega_id, self.entrega.pk)

    def test_tic_recepciona_conjunto_y_conserva_destinatario(self):
        confirmar_entrega(self.entrega.pk, self.tecnico)
        self.client.force_login(self.tecnico)
        response = self.client.get(self.url())
        self.assertContains(response, 'Recepcionar toda la entrega')
        self.assertTrue(response.context['puede_recibir'])
        self.client.post(self.url(), {'accion': 'recepcionar', 'conforme': 'si'})
        self.entrega.refresh_from_db()
        self.assertEqual(self.entrega.estado, 'recepcionada')
        self.assertEqual(self.entrega.funcionario, self.funcionario)
        self.assertEqual(self.entrega.recepcionado_por, self.tecnico)
        self.assertEqual(self.entrega.snapshot_acta['nombre_completo'], str(self.funcionario))
        self.assertEqual(self.entrega.snapshot_acta['recepcionado_por'], self.tecnico.get_username())
        self.assertEqual(self.entrega.movimientos.filter(recepcionado=True,
                                                         recepcionado_por=self.tecnico,
                                                         funcionario=self.funcionario).count(), 2)
        self.assertFalse(self.client.get(self.url()).context['puede_recibir'])

    def test_tic_no_recepciona_otro_establecimiento(self):
        confirmar_entrega(self.entrega.pk, self.tecnico)
        self.tecnico.establecimiento = self.otro_est
        self.tecnico.save()
        with self.assertRaises(PermissionDenied):
            recepcionar_entrega(self.entrega.pk, self.tecnico)
        self.assertFalse(self.entrega.movimientos.filter(recepcionado=True).exists())

    def test_datatable_listado_search(self):
        self.client.force_login(self.tecnico)
        url = reverse('gestion_tic:entrega_list')

        # GET request
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # POST with invalid action
        response = self.client.post(url, {'action': 'invalid'})
        self.assertEqual(response.status_code, 400)

        # POST search all
        response = self.client.post(url, {'action': 'search', 'draw': 1, 'start': 0, 'length': 10})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['draw'], 1)
        self.assertEqual(data['recordsTotal'], 1)
        self.assertEqual(data['recordsFiltered'], 1)
        self.assertEqual(len(data['data']), 1)
        item = data['data'][0]
        self.assertEqual(item['folio'], self.entrega.pk)
        self.assertEqual(item['estado'], 'borrador')
        self.assertIn('detalle_url', item)

        # POST search by term
        response = self.client.post(url, {
            'action': 'search', 'draw': 2, 'start': 0, 'length': 10,
            'search[value]': 'Persona receptora'
        })
        self.assertEqual(response.json()['recordsFiltered'], 1)

        response = self.client.post(url, {
            'action': 'search', 'draw': 3, 'start': 0, 'length': 10,
            'search[value]': 'Inexistente'
        })
        self.assertEqual(response.json()['recordsFiltered'], 0)

    def test_datatable_listado_column_control_and_permissions(self):
        # Create second entrega with another state
        func2 = Funcionario.objects.create(nombre='Otro funcionario', establecimiento=self.est)
        e2 = EntregaActivos.objects.create(
            funcionario=func2, tipo_movimiento=self.tipo_mov, jefe_firmante=self.jefe,
            establecimiento=self.est, estado=EntregaActivos.Estado.PENDIENTE
        )

        self.client.force_login(self.tecnico)
        url = reverse('gestion_tic:entrega_list')

        # Filter by estado 'borrador'
        response = self.client.post(url, {
            'action': 'search', 'draw': 1, 'start': 0, 'length': 10,
            'columns[2][columnControl][list]': ['borrador']
        })
        self.assertEqual(response.json()['recordsFiltered'], 1)
        self.assertEqual(response.json()['data'][0]['id'], self.entrega.pk)

        # Filter by estado 'pendiente'
        response = self.client.post(url, {
            'action': 'search', 'draw': 2, 'start': 0, 'length': 10,
            'columns[2][columnControl][list]': ['pendiente']
        })
        self.assertEqual(response.json()['recordsFiltered'], 1)
        self.assertEqual(response.json()['data'][0]['id'], e2.pk)

        # Non-manager user: only sees non-borrador for their funcionario
        self.client.force_login(self.receptor)
        response = self.client.post(url, {'action': 'search', 'draw': 3, 'start': 0, 'length': 10})
        # self.entrega is 'borrador' so receptor sees 0
        self.assertEqual(response.json()['recordsFiltered'], 0)

        # If self.entrega is confirmed -> pendiente, receptor sees it
        confirmar_entrega(self.entrega.pk, self.tecnico)
        response = self.client.post(url, {'action': 'search', 'draw': 4, 'start': 0, 'length': 10})
        self.assertEqual(response.json()['recordsFiltered'], 1)
