from django.test import TestCase, RequestFactory
from django.urls import reverse

from core.models.establecimientos import Establecimiento
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
        response = self.client.post(url, {'solucion': 'Se cambio el teclado'})
        self.assertEqual(response.status_code, 302)

        ticket.refresh_from_db()
        self.assertEqual(ticket.asignado_a, self.perfil_soporte)
        self.assertEqual(ticket.estado, 'CERRADO')
        self.assertFalse(ticket.is_active)
        self.assertIsNotNone(ticket.fecha_cierre)
        self.assertEqual(ticket.solucion, 'se cambio el teclado')

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

        # TicketEditorInactivosListView
        ticket.is_active = False
        ticket.save()
        url_inactivos = reverse('soporte:ticket_inactivos_list')
        response_inactivos = self.client.get(url_inactivos)
        self.assertEqual(response_inactivos.status_code, 200)
