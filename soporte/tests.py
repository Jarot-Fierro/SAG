from unittest.mock import patch

from django.test import TestCase, RequestFactory
from django.urls import reverse
from soporte.tickets import serialize_ticket

from core.models.configuracion_correo import ConfiguracionCorreo
from core.models.establecimientos import Establecimiento
from core.models.funcionario import Funcionario
from core.models.unidad_organizacional import UnidadOrganizacional
from core.models.usuarios import User
from soporte.forms.forms_tickets import FormTicketEditor
from soporte.models import Ticket, AreaSoporte, TipoSoporte, PerfilSoporte, TicketConfig


class SoportePerfilSoporteTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.establecimiento = Establecimiento.objects.create(
            nombre="Hospital Base",
            alias="HB",
            region="Coquimbo"
        )
        self.user_solicitante = User.objects.create_user(
            username="solicitante",
            password="password123",
            first_name="Juan",
            last_name="Perez",
            establecimiento=self.establecimiento
        )
        self.user_soporte = User.objects.create_user(
            username="tecnico",
            password="password123",
            first_name="Carlos",
            last_name="Gomez",
            establecimiento=self.establecimiento,
            is_staff=True
        )
        self.area_soporte = AreaSoporte.objects.create(
            nombre="Informatica",
            establecimiento=self.establecimiento
        )
        self.tipo_soporte = TipoSoporte.objects.create(
            nombre="Hardware",
            establecimiento=self.establecimiento
        )
        self.tipo_soporte.area_soporte.add(self.area_soporte)
        self.perfil_soporte = PerfilSoporte.objects.create(
            usuario=self.user_soporte
        )
        self.perfil_soporte.area_soporte.add(self.area_soporte)

    def test_perfil_soporte_str_and_relation(self):
        self.assertEqual(str(self.perfil_soporte), "CARLOS GOMEZ")

        ticket = Ticket.objects.create(
            titulo="Problema monitor",
            descripcion="No enciende la pantalla",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte,
            tipo_soporte=self.tipo_soporte,
            asignado_a=self.perfil_soporte
        )

        self.assertEqual(ticket.asignado_a, self.perfil_soporte)
        self.assertIn(ticket, self.perfil_soporte.tickets_asignados.all())

    def test_form_ticket_editor_with_perfil_soporte(self):
        ticket = Ticket.objects.create(
            titulo="Problema red",
            descripcion="Sin conexion",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte,
            tipo_soporte=self.tipo_soporte
        )

        request = self.factory.get('/')
        request.user = self.user_soporte

        form = FormTicketEditor(
            data={
                'numero_ticket': ticket.numero_ticket,
                'establecimiento': self.establecimiento.pk,
                'titulo': 'Problema red modificado',
                'funcionario': self.user_solicitante.pk,
                'area_soporte': self.area_soporte.pk,
                'estado': 'EN PROCESO',
                'asignado_a': self.perfil_soporte.pk,
                'tipo_soporte': self.tipo_soporte.pk,
                'descripcion': 'Sin conexion a internet',
                'solucion': ''
            },
            instance=ticket,
            request=request
        )

        self.assertTrue(form.is_valid(), form.errors)
        saved_ticket = form.save()
        self.assertEqual(saved_ticket.asignado_a, self.perfil_soporte)
        self.assertEqual(saved_ticket.estado, 'EN PROCESO')

    def test_ticket_tomar_view(self):
        ticket = Ticket.objects.create(
            titulo="Impresora no funciona",
            descripcion="Falta toner",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte
        )

        self.client.force_login(self.user_soporte)
        url = reverse('soporte:ticket_tomar', kwargs={'pk': ticket.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        ticket.refresh_from_db()
        self.assertEqual(ticket.asignado_a, self.perfil_soporte)
        self.assertEqual(ticket.estado, 'EN PROCESO')

    def test_ticket_cerrar_view(self):
        ticket = Ticket.objects.create(
            titulo="Teclado danado",
            descripcion="Tecla rota",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte
        )

        self.client.force_login(self.user_soporte)
        url = reverse('soporte:ticket_cerrar', kwargs={'pk': ticket.pk})
        response = self.client.post(url, {
            'solucion': 'Se cambio el teclado',
            'tipo_soporte': self.tipo_soporte.pk,
        })
        self.assertEqual(response.status_code, 302)

        ticket.refresh_from_db()
        self.assertEqual(ticket.asignado_a, self.perfil_soporte)
        self.assertEqual(ticket.estado, 'CERRADO')
        self.assertFalse(ticket.is_active)
        self.assertIsNotNone(ticket.fecha_cierre)
        self.assertEqual(ticket.solucion, 'se cambio el teclado')
        self.assertEqual(ticket.tipo_soporte, self.tipo_soporte)

    def test_ticket_dashboard_view(self):
        Ticket.objects.create(
            titulo="Ticket abierto",
            descripcion="Desc",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte,
            asignado_a=self.perfil_soporte,
            estado='ABIERTO'
        )
        Ticket.objects.create(
            titulo="Ticket cerrado",
            descripcion="Desc",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte,
            asignado_a=self.perfil_soporte,
            estado='CERRADO'
        )

        self.client.force_login(self.user_soporte)
        url = reverse('soporte:ticket_dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('bar_chart_data', response.context)
        bar_data = response.context['bar_chart_data']
        self.assertEqual(len(bar_data), 1)
        self.assertEqual(bar_data[0]['usuario'], 'CARLOS GOMEZ')
        self.assertEqual(bar_data[0]['abiertos'], 1)
        self.assertEqual(bar_data[0]['cerrados'], 1)

    def test_tipo_soporte_filtrado_por_area_soporte_perfil(self):
        area_mantencion = AreaSoporte.objects.create(
            nombre="Mantencion",
            establecimiento=self.establecimiento
        )
        tipo_red = TipoSoporte.objects.create(
            nombre="Problema de red",
            establecimiento=self.establecimiento
        )
        tipo_red.area_soporte.add(area_mantencion)

        self.client.force_login(self.user_soporte)
        url_editor = reverse('soporte:ticket_editor_list')
        response = self.client.get(url_editor)

        self.assertEqual(response.status_code, 200)
        tipos = list(response.context['tipos_soporte'])
        self.assertIn(self.tipo_soporte, tipos)
        self.assertNotIn(tipo_red, tipos)

        # Si a "Problema de red" le asignamos "Informatica", ahora sí debe listarse
        tipo_red.area_soporte.add(self.area_soporte)
        response = self.client.get(url_editor)
        tipos = list(response.context['tipos_soporte'])
        self.assertIn(tipo_red, tipos)
        self.assertIn(self.tipo_soporte, tipos)

    def test_ticket_historial_timeline(self):
        ticket = Ticket.objects.create(
            titulo="Falla de red",
            descripcion="Sin acceso a internet",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte,
            estado='ABIERTO'
        )

        ticket.asignado_a = self.perfil_soporte
        ticket.save()

        ticket.estado = 'EN PROCESO'
        ticket.save()

        ticket.estado = 'ESPERA'
        ticket.save()

        ticket.estado = 'EN PROCESO'
        ticket.save()

        ticket.estado = 'CERRADO'
        ticket.solucion = 'Problema solucionado'
        ticket.save()

        self.client.force_login(self.user_soporte)
        url_historial = reverse('soporte:ticket_historial', kwargs={'pk': ticket.pk})
        response = self.client.get(url_historial)

        self.assertEqual(response.status_code, 200)
        self.assertIn('eventos', response.context)
        eventos = response.context['eventos']

        titulos = [e['titulo'] for e in eventos]
        self.assertIn('Ticket creado', titulos)
        self.assertIn('Ticket asignado', titulos)
        self.assertIn('En proceso', titulos)
        self.assertIn('En espera', titulos)
        self.assertIn('Cerrado', titulos)

        detalles = [e['detalle'] for e in eventos]
        self.assertIn('Solicitud ingresada', detalles)
        self.assertIn(f'Asignado a {self.perfil_soporte}', detalles)
        self.assertIn('Técnico comenzó la atención', detalles)
        self.assertIn('Esperando información del usuario', detalles)
        self.assertIn('Atención retomada', detalles)
        self.assertIn('problema solucionado', [d.lower() for d in detalles])

    @patch('core.services.email_service.EmailService.send_email_with_config')
    def test_ticket_create_envia_correo_exitosamente(self, mock_send_email):
        mock_send_email.return_value = True

        config_correo = ConfiguracionCorreo.objects.create(
            establecimiento=self.establecimiento,
            nombre_remitente="Mesa de Ayuda SAG",
            email_remitente="soporte@sag.cl",
            smtp_host="smtp.sag.cl",
            smtp_port=587,
            smtp_usuario="soporte@sag.cl",
            _smtp_password="password123",
            activo=True
        )

        uo = UnidadOrganizacional.objects.create(
            nombre="Departamento de Informatica",
            establecimiento=self.establecimiento,
            es_departamento=True
        )
        funcionario = Funcionario.objects.create(
            nombres="Juan",
            apellidos="Perez",
            unidad_organizacional=uo,
            establecimiento=self.establecimiento
        )
        self.user_solicitante.funcionario = funcionario
        self.user_solicitante.email = "juan.perez@sag.cl"
        self.user_solicitante.save()

        self.client.force_login(self.user_solicitante)
        url_create = reverse('soporte:ticket_create')

        response = self.client.post(url_create, {
            'titulo': 'Problema con la impresora de red',
            'descripcion': 'No imprime documentos PDF',
            'area_soporte': self.area_soporte.pk,
        })

        self.assertEqual(response.status_code, 302)

        ticket = Ticket.objects.filter(titulo__icontains='Problema con la impresora').first()
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.funcionario, self.user_solicitante)
        self.assertEqual(ticket.establecimiento, self.establecimiento)
        self.assertTrue(ticket.numero_ticket.startswith('TCK-'))

        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args[1] if mock_send_email.call_args[1] else {}
        call_args = mock_send_email.call_args[0] if mock_send_email.call_args[0] else ()

        config_passed = call_kwargs.get('config') or (call_args[0] if len(call_args) > 0 else None)
        subject_passed = call_kwargs.get('subject') or (call_args[1] if len(call_args) > 1 else None)
        recipient_passed = call_kwargs.get('recipient_list') or (call_args[2] if len(call_args) > 2 else None)
        context_passed = call_kwargs.get('context') or (call_args[4] if len(call_args) > 4 else None)

        self.assertEqual(config_passed, config_correo)
        self.assertIn(ticket.numero_ticket, subject_passed)
        self.assertEqual(recipient_passed, ['juan.perez@sag.cl'])
        self.assertEqual(context_passed['ticket'], ticket)
        self.assertEqual(context_passed['usuario'], self.user_solicitante)
        self.assertIn(uo.nombre, str(context_passed['departamento']))

    @patch('core.services.email_service.EmailService.send_email_with_config')
    def test_ticket_create_falla_correo_no_impide_creacion(self, mock_send_email):
        mock_send_email.side_effect = Exception("Fallo de conexión SMTP")

        ConfiguracionCorreo.objects.create(
            establecimiento=self.establecimiento,
            nombre_remitente="Mesa de Ayuda SAG",
            email_remitente="soporte@sag.cl",
            smtp_host="smtp.sag.cl",
            smtp_port=587,
            smtp_usuario="soporte@sag.cl",
            _smtp_password="password123",
            activo=True
        )

        self.user_solicitante.email = "juan.perez@sag.cl"
        self.user_solicitante.save()

        self.client.force_login(self.user_solicitante)
        url_create = reverse('soporte:ticket_create')

        response = self.client.post(url_create, {
            'titulo': 'Error en pantalla azul',
            'descripcion': 'Se reinicia continuamente',
            'area_soporte': self.area_soporte.pk,
        })

        self.assertEqual(response.status_code, 302)

        ticket = Ticket.objects.filter(titulo__icontains='Error en pantalla azul').first()
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.funcionario, self.user_solicitante)

    @patch('core.services.email_service.EmailService.send_email_with_config')
    def test_ticket_para_funcionario_create_envia_correo_a_correo_especificado(self, mock_send_email):
        mock_send_email.return_value = True

        config_correo = ConfiguracionCorreo.objects.create(
            establecimiento=self.establecimiento,
            nombre_remitente="Mesa de Ayuda SAG",
            email_remitente="soporte@sag.cl",
            smtp_host="smtp.sag.cl",
            smtp_port=587,
            smtp_usuario="soporte@sag.cl",
            _smtp_password="password123",
            activo=True
        )

        uo = UnidadOrganizacional.objects.create(
            nombre="Departamento de Finanzas",
            establecimiento=self.establecimiento,
            es_departamento=True
        )

        self.client.force_login(self.user_solicitante)
        url_create_para_funcionario = reverse('soporte:ticket_para_funcionario_create')

        response = self.client.post(url_create_para_funcionario, {
            'titulo': 'Problema externo',
            'descripcion': 'Fallo en equipo',
            'area_soporte': self.area_soporte.pk,
            'nombres': 'Pedro Gonzalez',
            'correo': 'pedro.gonzalez@externo.cl',
            'departamento': uo.pk,
        })

        self.assertEqual(response.status_code, 302)

        ticket = Ticket.objects.filter(nombres='Pedro Gonzalez').first()
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.nombres, 'Pedro Gonzalez')
        self.assertEqual(ticket.correo, 'pedro.gonzalez@externo.cl')
        self.assertIn('Departamento de Finanzas', ticket.departamento)

        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args[1] if mock_send_email.call_args[1] else {}
        call_args = mock_send_email.call_args[0] if mock_send_email.call_args[0] else ()

        config_passed = call_kwargs.get('config') or (call_args[0] if len(call_args) > 0 else None)
        subject_passed = call_kwargs.get('subject') or (call_args[1] if len(call_args) > 1 else None)
        recipient_passed = call_kwargs.get('recipient_list') or (call_args[2] if len(call_args) > 2 else None)
        context_passed = call_kwargs.get('context') or (call_args[4] if len(call_args) > 4 else None)

        self.assertEqual(config_passed, config_correo)
        self.assertIn(ticket.numero_ticket, subject_passed)
        self.assertEqual(recipient_passed, ['pedro.gonzalez@externo.cl'])
        self.assertEqual(context_passed['ticket'], ticket)
        self.assertIn('Departamento de Finanzas', str(context_passed['departamento']))

    def test_ticket_delete_view_desactiva_ticket(self):
        ticket = Ticket.objects.create(
            titulo="Ticket para desactivar",
            descripcion="Descripción de prueba",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte,
            is_active=True
        )

        self.client.force_login(self.user_solicitante)
        url_delete = reverse('soporte:ticket_delete', kwargs={'pk': ticket.pk})
        url_list = reverse('soporte:ticket_list')

        response = self.client.get(url_delete, HTTP_REFERER=url_list, follow=True)
        self.assertEqual(response.status_code, 200)

        ticket.refresh_from_db()
        self.assertFalse(ticket.is_active)
        self.assertEqual(ticket.estado, 'CANCELADO')
        self.assertContains(response, 'Ticket desactivado correctamente')

    def test_ticket_deactivate_ajax_post(self):
        ticket = Ticket.objects.create(
            titulo="Ticket para desactivar ajax",
            descripcion="Descripción de prueba",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte,
            is_active=True
        )

        self.client.force_login(self.user_solicitante)
        url_deactivate = reverse('soporte:ticket_deactivate', kwargs={'pk': ticket.pk})

        response = self.client.post(
            url_deactivate,
            {'id': ticket.pk},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 'success')
        self.assertIn('desactivado correctamente', data['message'])

        ticket.refresh_from_db()
        self.assertFalse(ticket.is_active)
        self.assertEqual(ticket.estado, 'CANCELADO')


class SoporteDataTablesTests(TestCase):
    def setUp(self):
        self.establecimiento = Establecimiento.objects.create(
            nombre="Hospital Base",
            alias="HB",
            region="Coquimbo"
        )
        self.otro_establecimiento = Establecimiento.objects.create(
            nombre="Hospital Norte",
            alias="HN",
            region="Antofagasta"
        )
        self.user_solicitante = User.objects.create_user(
            username="solicitante",
            password="password123",
            first_name="Juan",
            last_name="Perez",
            establecimiento=self.establecimiento
        )
        self.funcionario_solicitante = Funcionario.objects.create(
            nombres="Juan",
            apellidos="Perez",
            establecimiento=self.establecimiento
        )
        self.user_solicitante.funcionario = self.funcionario_solicitante
        self.user_solicitante.save()

        self.user_soporte = User.objects.create_user(
            username="tecnico",
            password="password123",
            first_name="Carlos",
            last_name="Gomez",
            establecimiento=self.establecimiento,
            is_staff=True
        )
        self.funcionario_soporte = Funcionario.objects.create(
            nombres="Carlos",
            apellidos="Gomez",
            establecimiento=self.establecimiento
        )
        self.user_soporte.funcionario = self.funcionario_soporte
        self.user_soporte.save()
        self.area_soporte = AreaSoporte.objects.create(
            nombre="Informatica",
            establecimiento=self.establecimiento
        )
        self.tipo_soporte = TipoSoporte.objects.create(
            nombre="Hardware",
            establecimiento=self.establecimiento
        )
        self.tipo_soporte.area_soporte.add(self.area_soporte)
        self.perfil_soporte = PerfilSoporte.objects.create(
            usuario=self.user_soporte
        )
        self.perfil_soporte.area_soporte.add(self.area_soporte)

        # Tickets de prueba
        self.ticket_activo1 = Ticket.objects.create(
            titulo="Problema de red en piso 1",
            descripcion="Sin acceso a internet",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte,
            estado='ABIERTO',
            is_active=True
        )
        self.ticket_activo2 = Ticket.objects.create(
            titulo="Problema impresora farmacia",
            descripcion="Atasco de papel",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte,
            asignado_a=self.perfil_soporte,
            estado='EN PROCESO',
            is_active=True
        )
        self.ticket_cerrado = Ticket.objects.create(
            titulo="Cambio de teclado",
            descripcion="Tecla rota",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte,
            asignado_a=self.perfil_soporte,
            estado='CERRADO',
            is_active=False
        )
        self.ticket_otro_est = Ticket.objects.create(
            titulo="Ticket otro hospital",
            descripcion="No debe ser visible",
            establecimiento=self.otro_establecimiento,
            estado='ABIERTO',
            is_active=True
        )

    def test_serializer_ticket_fields_and_formats(self):
        data = serialize_ticket(self.ticket_activo1)
        self.assertEqual(data["id"], self.ticket_activo1.pk)
        self.assertEqual(data["numero_ticket"], self.ticket_activo1.numero_ticket)
        self.assertEqual(data["titulo"].upper(), "PROBLEMA DE RED EN PISO 1")
        self.assertEqual(data["nombres"].upper(), "JUAN PEREZ")
        self.assertEqual(data["estado"], "ABIERTO")
        self.assertEqual(data["area_soporte"].upper(), "INFORMATICA")
        self.assertIsNone(data["asignado_a"])
        self.assertIsNotNone(data["created_at"])
        self.assertIsNone(data["fecha_cierre"])
        self.assertTrue(data["is_active"])

    def test_ticket_list_html_and_ajax_datatables(self):
        self.client.force_login(self.user_solicitante)
        url = reverse('soporte:ticket_list')

        # 1. Petición GET estándar (renderiza HTML con DataTables)
        response_html = self.client.get(url)
        self.assertEqual(response_html.status_code, 200)
        self.assertContains(response_html, "myTable")
        self.assertContains(response_html, "ticket_datatable.js")
        self.assertContains(response_html, "ticket_modal.js")

        # 2. Petición POST DataTables server-side (action=search)
        response_post = self.client.post(
            url,
            {"action": "search", "draw": "1", "start": "0", "length": "10"}
        )
        self.assertEqual(response_post.status_code, 200)
        data_post = response_post.json()
        self.assertEqual(data_post["draw"], 1)
        self.assertEqual(data_post["recordsTotal"], 2)
        self.assertEqual(data_post["recordsFiltered"], 2)
        self.assertEqual(len(data_post["data"]), 2)

        # 3. Petición AJAX DataTables GET compatibilidad
        response_ajax = self.client.get(
            url,
            {"draw": "1", "start": "0", "length": "10"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response_ajax.status_code, 200)
        data = response_ajax.json()

        self.assertEqual(data["draw"], 1)
        # Solo tickets activos de su establecimiento (2 tickets activos)
        self.assertEqual(data["recordsTotal"], 2)
        self.assertEqual(data["recordsFiltered"], 2)
        self.assertEqual(len(data["data"]), 2)

    def test_ticket_list_ajax_search_and_ordering(self):
        self.client.force_login(self.user_solicitante)
        url = reverse('soporte:ticket_list')

        # Búsqueda global por término "impresora"
        response_search = self.client.get(
            url,
            {"draw": "2", "start": "0", "length": "10", "search[value]": "impresora"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response_search.status_code, 200)
        data = response_search.json()
        self.assertEqual(data["recordsFiltered"], 1)
        self.assertEqual(data["data"][0]["titulo"].upper(), "PROBLEMA IMPRESORA FARMACIA")

        # Ordenamiento ascendente por titulo (columna 1)
        response_order = self.client.get(
            url,
            {"draw": "3", "start": "0", "length": "10", "order[0][column]": "1", "order[0][dir]": "asc"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response_order.status_code, 200)
        data_order = response_order.json()
        self.assertEqual(len(data_order["data"]), 2)
        self.assertEqual(data_order["data"][0]["titulo"].upper(), "PROBLEMA DE RED EN PISO 1")
        self.assertEqual(data_order["data"][1]["titulo"].upper(), "PROBLEMA IMPRESORA FARMACIA")

    def test_ticket_list_post_search_and_column_control(self):
        self.client.force_login(self.user_solicitante)
        url = reverse('soporte:ticket_list')

        # 1. Búsqueda por término global vía POST DataTables
        response_search = self.client.post(
            url,
            {"action": "search", "draw": "2", "start": "0", "length": "10", "search[value]": "impresora"}
        )
        self.assertEqual(response_search.status_code, 200)
        data = response_search.json()
        self.assertEqual(data["recordsFiltered"], 1)
        self.assertEqual(data["data"][0]["titulo"].upper(), "PROBLEMA IMPRESORA FARMACIA")

        # 2. Filtro columnControl por estado (columna 3)
        response_filter = self.client.post(
            url,
            {"action": "search", "draw": "3", "start": "0", "length": "10",
             "columns[3][columnControl][list]": ["EN PROCESO"]}
        )
        self.assertEqual(response_filter.status_code, 200)
        data_filtered = response_filter.json()
        self.assertEqual(data_filtered["recordsFiltered"], 1)
        self.assertEqual(data_filtered["data"][0]["estado"], "EN PROCESO")

    def test_ticket_update_view_get_and_post(self):
        self.client.force_login(self.user_solicitante)
        url_update = reverse('soporte:ticket_update', kwargs={'pk': self.ticket_activo1.pk})

        # GET form
        response_get = self.client.get(url_update)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "ticket_form.js")
        self.assertContains(response_get, self.ticket_activo1.titulo)

        # POST update
        response_post = self.client.post(url_update, {
            'titulo': 'Problema de red actualizado',
            'area_soporte': self.area_soporte.pk,
            'descripcion': 'Descripcion actualizada'
        })
        self.assertEqual(response_post.status_code, 302)
        self.ticket_activo1.refresh_from_db()
        self.assertEqual(self.ticket_activo1.titulo, 'PROBLEMA DE RED ACTUALIZADO')

    def test_ticket_editor_list_html_and_ajax_datatables(self):
        self.client.force_login(self.user_soporte)
        url = reverse('soporte:ticket_editor_list')

        # GET HTML
        response_html = self.client.get(url)
        self.assertEqual(response_html.status_code, 200)
        self.assertContains(response_html, "table-datatable")
        self.assertIn("tipos_soporte", response_html.context)

        # GET AJAX
        response_ajax = self.client.get(
            url,
            {"draw": "1", "start": "0", "length": "10"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response_ajax.status_code, 200)
        data = response_ajax.json()
        self.assertEqual(data["recordsTotal"], 2)
        self.assertEqual(len(data["data"]), 2)

    def test_ticket_editor_inactivos_list_html_and_ajax_datatables(self):
        self.client.force_login(self.user_soporte)
        url = reverse('soporte:ticket_inactivos_list')

        # GET HTML
        response_html = self.client.get(url)
        self.assertEqual(response_html.status_code, 200)
        self.assertContains(response_html, "table-datatable")

        # GET AJAX
        response_ajax = self.client.get(
            url,
            {"draw": "1", "start": "0", "length": "10"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response_ajax.status_code, 200)
        data = response_ajax.json()
        self.assertEqual(data["recordsTotal"], 1)
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["titulo"].upper(), "CAMBIO DE TECLADO")
        self.assertFalse(data["data"][0]["is_active"])

    def test_soporte_list_v2_view(self):
        self.client.force_login(self.user_solicitante)
        url = reverse('soporte:ticket_v2')

        response_html = self.client.get(url)
        self.assertEqual(response_html.status_code, 200)
        self.assertContains(response_html, "table-datatable")

        response_ajax = self.client.get(
            url,
            {"draw": "1", "start": "0", "length": "10"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response_ajax.status_code, 200)
        data = response_ajax.json()
        self.assertEqual(data["recordsTotal"], 2)

    def test_models_to_json(self):
        # 1. TicketConfig
        config, _ = TicketConfig.objects.get_or_create(
            establecimiento=self.establecimiento,
            defaults={'ultimo_correlativo': 10}
        )
        config.ultimo_correlativo = 10
        config.save()
        config_json = config.toJSON()
        self.assertIsInstance(config_json, dict)
        self.assertEqual(config_json['ultimo_correlativo'], 10)
        self.assertEqual(config_json['establecimiento']['id'], self.establecimiento.pk)

        # 2. PerfilSoporte
        with patch.object(User, 'toJSON', return_value={'id': self.user_soporte.pk, 'username': 'tecnico'}):
            perfil_json = self.perfil_soporte.toJSON()
            self.assertIsInstance(perfil_json, dict)
            self.assertEqual(perfil_json['usuario']['id'], self.user_soporte.pk)

        # 3. TipoSoporte
        tipo_json = self.tipo_soporte.toJSON()
        self.assertIsInstance(tipo_json, dict)
        self.assertEqual(tipo_json['nombre'], 'HARDWARE')
        self.assertEqual(tipo_json['establecimiento']['id'], self.establecimiento.pk)

        # 4. AreaSoporte
        area_json = self.area_soporte.toJSON()
        self.assertIsInstance(area_json, dict)
        self.assertEqual(area_json['nombre'], 'INFORMATICA')
        self.assertEqual(area_json['establecimiento']['id'], self.establecimiento.pk)

        # 5. Ticket
        self.ticket_activo1.tipo_soporte = self.tipo_soporte
        self.ticket_activo1.asignado_a = self.perfil_soporte
        self.ticket_activo1.save()

        with patch.object(User, 'toJSON', return_value={'id': self.user_solicitante.pk, 'username': 'solicitante'}):
            ticket_json = self.ticket_activo1.toJSON()
            self.assertIsInstance(ticket_json, dict)
            self.assertEqual(ticket_json['titulo'], 'PROBLEMA DE RED EN PISO 1')
            self.assertEqual(ticket_json['establecimiento']['id'], self.establecimiento.pk)
            self.assertEqual(ticket_json['funcionario']['id'], self.user_solicitante.pk)
            self.assertEqual(ticket_json['area_soporte']['id'], self.area_soporte.pk)
            self.assertEqual(ticket_json['tipo_soporte']['id'], self.tipo_soporte.pk)
            self.assertEqual(ticket_json['asignado_a']['id'], self.perfil_soporte.pk)

    def test_ticket_editor_list_post_datatables(self):
        self.client.force_login(self.user_soporte)
        url = reverse('soporte:ticket_editor_list')

        # POST search
        response_post = self.client.post(
            url,
            {"action": "search", "draw": "1", "start": "0", "length": "10"}
        )
        self.assertEqual(response_post.status_code, 200)
        data = response_post.json()
        self.assertEqual(data["draw"], 1)
        self.assertEqual(data["recordsTotal"], 2)
        self.assertEqual(len(data["data"]), 2)
        self.assertIn("columnControl", data)

    def test_ticket_editor_inactivos_list_post_datatables(self):
        self.client.force_login(self.user_soporte)
        url = reverse('soporte:ticket_inactivos_list')

        # POST search
        response_post = self.client.post(
            url,
            {"action": "search", "draw": "1", "start": "0", "length": "10"}
        )
        self.assertEqual(response_post.status_code, 200)
        data = response_post.json()
        self.assertEqual(data["draw"], 1)
        self.assertEqual(data["recordsTotal"], 1)
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["titulo"].upper(), "CAMBIO DE TECLADO")
