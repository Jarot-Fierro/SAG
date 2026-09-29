from unittest.mock import patch

from django.test import TestCase, RequestFactory
from django.urls import reverse

from core.models.configuracion_correo import ConfiguracionCorreo
from core.models.establecimientos import Establecimiento
from core.models.funcionario import Funcionario
from core.models.unidad_organizacional import UnidadOrganizacional
from core.models.usuarios import User
from soporte.forms.forms_tickets import FormTicketEditor
from soporte.models import Ticket, AreaSoporte, TipoSoporte, PerfilSoporte


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
                'estado': 'EN_PROCESO',
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
        self.assertEqual(saved_ticket.estado, 'EN_PROCESO')

    def test_ticket_tomar_view(self):
        ticket = Ticket.objects.create(
            titulo="Impresora no funciona",
            descripcion="Falta toner",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte
        )

        self.client.login(username="tecnico", password="password123")
        url = reverse('soporte:ticket_tomar', kwargs={'pk': ticket.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        ticket.refresh_from_db()
        self.assertEqual(ticket.asignado_a, self.perfil_soporte)

    def test_ticket_cerrar_view(self):
        ticket = Ticket.objects.create(
            titulo="Teclado danado",
            descripcion="Tecla rota",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte
        )

        self.client.login(username="tecnico", password="password123")
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
        ticket = Ticket.objects.create(
            titulo="Ticket abierto",
            descripcion="Desc",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte,
            asignado_a=self.perfil_soporte,
            estado='ABIERTO'
        )
        ticket_cerrado = Ticket.objects.create(
            titulo="Ticket cerrado",
            descripcion="Desc",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte,
            asignado_a=self.perfil_soporte,
            estado='CERRADO'
        )

        self.client.login(username="tecnico", password="password123")
        url = reverse('soporte:ticket_dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('bar_chart_data', response.context)
        bar_data = response.context['bar_chart_data']
        self.assertEqual(len(bar_data), 1)
        self.assertEqual(bar_data[0]['usuario'], 'CARLOS GOMEZ')
        self.assertEqual(bar_data[0]['abiertos'], 1)
        self.assertEqual(bar_data[0]['cerrados'], 1)

    def test_ticket_list_views(self):
        ticket = Ticket.objects.create(
            titulo="Ticket para listar",
            descripcion="Desc",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte,
            asignado_a=self.perfil_soporte,
            estado='ABIERTO'
        )

        self.client.login(username="tecnico", password="password123")

        # TicketListView
        url = reverse('soporte:ticket_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # TicketEditorListView
        url_editor = reverse('soporte:ticket_editor_list')
        response_editor = self.client.get(url_editor)
        self.assertEqual(response_editor.status_code, 200)
        self.assertIn('tipos_soporte', response_editor.context)
        self.assertContains(response_editor, 'name="tipo_soporte"')

        # TicketEditorInactivosListView
        ticket.is_active = False
        ticket.save()
        url_inactivos = reverse('soporte:ticket_inactivos_list')
        response_inactivos = self.client.get(url_inactivos)
        self.assertEqual(response_inactivos.status_code, 200)

    def test_tipo_soporte_filtrado_por_area_soporte_perfil(self):
        area_mantencion = AreaSoporte.objects.create(
            nombre="Mantencion",
            establecimiento=self.establecimiento
        )
        tipo_red = TipoSoporte.objects.create(
            nombre="Problema de red",
            establecimiento=self.establecimiento
        )
        # Asociado solo a mantención inicialmente
        tipo_red.area_soporte.add(area_mantencion)

        self.client.login(username="tecnico", password="password123")
        url_editor = reverse('soporte:ticket_editor_list')
        response = self.client.get(url_editor)

        # El técnico solo tiene informática, no debe ver "Problema de red"
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
        # 1. Creación
        ticket = Ticket.objects.create(
            titulo="Falla de red",
            descripcion="Sin acceso a internet",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte,
            estado='ABIERTO'
        )

        # 2. Asignación
        ticket.asignado_a = self.perfil_soporte
        ticket.save()

        # 3. En Proceso
        ticket.estado = 'EN_PROCESO'
        ticket.save()

        # 4. En Espera
        ticket.estado = 'ESPERA'
        ticket.save()

        # 5. En Proceso (retomado)
        ticket.estado = 'EN_PROCESO'
        ticket.save()

        # 6. Cerrado
        ticket.estado = 'CERRADO'
        ticket.solucion = 'Problema solucionado'
        ticket.save()

        self.client.login(username="tecnico", password="password123")
        url_historial = reverse('soporte:ticket_historial', kwargs={'pk': ticket.pk})
        response = self.client.get(url_historial)

        self.assertEqual(response.status_code, 200)
        self.assertIn('eventos', response.context)
        eventos = response.context['eventos']

        # Verificar títulos esperados en la línea de tiempo
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

        # Verificar que list.html contiene el botón de historial
        response_list = self.client.get(reverse('soporte:ticket_list'))
        self.assertEqual(response_list.status_code, 200)
        self.assertContains(response_list, url_historial)
        self.assertContains(response_list, 'bi-clock-history')

    @patch('core.services.email_service.EmailService.send_email_with_config')
    def test_ticket_create_envia_correo_exitosamente(self, mock_send_email):
        mock_send_email.return_value = True

        # Crear configuración de correo para el establecimiento
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

        # Crear departamento y asociarlo al funcionario del usuario
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

        self.client.login(username="solicitante", password="password123")
        url_create = reverse('soporte:ticket_create')

        response = self.client.post(url_create, {
            'titulo': 'Problema con la impresora de red',
            'descripcion': 'No imprime documentos PDF',
            'area_soporte': self.area_soporte.pk,
        })

        # Redirección tras creación exitosa
        self.assertEqual(response.status_code, 302)

        # Verificar que el ticket fue creado
        ticket = Ticket.objects.filter(titulo__icontains='Problema con la impresora').first()
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.funcionario, self.user_solicitante)
        self.assertEqual(ticket.establecimiento, self.establecimiento)
        self.assertTrue(ticket.numero_ticket.startswith('TCK-'))

        # Verificar que send_email_with_config fue invocado con los parámetros correctos
        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args[1] if mock_send_email.call_args[1] else {}
        call_args = mock_send_email.call_args[0] if mock_send_email.call_args[0] else ()

        # Revisar argumentos posicionales o por nombre
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
        # Simular que el envío de correo lanza una excepción
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

        self.client.login(username="solicitante", password="password123")
        url_create = reverse('soporte:ticket_create')

        response = self.client.post(url_create, {
            'titulo': 'Error en pantalla azul',
            'descripcion': 'Se reinicia continuamente',
            'area_soporte': self.area_soporte.pk,
        })

        # Debe responder con 302 exitoso (no crash 500)
        self.assertEqual(response.status_code, 302)

        # El ticket debe existir en la BD
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

        self.client.login(username="solicitante", password="password123")
        url_create_para_funcionario = reverse('soporte:ticket_para_funcionario_create')

        response = self.client.post(url_create_para_funcionario, {
            'titulo': 'Problema externo',
            'descripcion': 'Fallo en equipo',
            'area_soporte': self.area_soporte.pk,
            'nombres': 'Pedro',
            'apellidos': 'González',
            'correo': 'pedro.gonzalez@externo.cl',
            'departamento': uo.pk,
        })

        self.assertEqual(response.status_code, 302)

        ticket = Ticket.objects.filter(titulo='Problema externo').first()
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.nombres, 'Pedro')
        self.assertEqual(ticket.apellidos, 'González')
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

        self.client.login(username="solicitante", password="password123")
        url_delete = reverse('soporte:ticket_delete', kwargs={'pk': ticket.pk})
        url_list = reverse('soporte:ticket_list')

        response = self.client.get(url_delete, HTTP_REFERER=url_list, follow=True)
        self.assertEqual(response.status_code, 200)

        ticket.refresh_from_db()
        self.assertFalse(ticket.is_active)
        self.assertContains(response, 'Ticket desactivado correctamente')

    def test_ticket_list_shows_delete_button_for_active_ticket(self):
        ticket = Ticket.objects.create(
            titulo="Ticket en lista",
            descripcion="Descripción en lista",
            establecimiento=self.establecimiento,
            funcionario=self.user_solicitante,
            area_soporte=self.area_soporte,
            is_active=True
        )

        self.client.login(username="solicitante", password="password123")
        url_list = reverse('soporte:ticket_list')

        response = self.client.get(url_list)
        self.assertEqual(response.status_code, 200)
        url_delete = reverse('soporte:ticket_delete', kwargs={'pk': ticket.pk})
        self.assertContains(response, url_delete)
        self.assertContains(response, 'Desactivar')
