from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from agenda_telefonica.forms import FormAnexos
from agenda_telefonica.models import Anexo, PerfilAgenda
from core.models.establecimientos import Establecimiento
from core.models.funcionario import Funcionario
from core.models.rol_organizacional import RolOrganizacional
from core.models.unidad_organizacional import UnidadOrganizacional

User = get_user_model()


class FormAnexosTest(TestCase):
    def setUp(self):
        self.est1 = Establecimiento.objects.create(nombre="Establecimiento 1")
        self.uo1 = UnidadOrganizacional.objects.create(nombre="UO 1", establecimiento=self.est1)
        self.rol1 = RolOrganizacional.objects.create(nombre="Rol 1")

    def test_form_valid(self):
        form = FormAnexos(data={
            'anexo': '1234',
            'anexo_publico': '5678',
            'numero_telefonico': '99999999',
            'nombre_anexo': 'Anexo Prueba',
            'email': 'test@example.com',
            'rol_organizacional': self.rol1.id,
            'encargado_de': 'Jefe',
            'unidad_organizacional': self.uo1.id,
            'establecimiento': self.est1.id,
            'is_active': True,
        })
        self.assertTrue(form.is_valid(), form.errors)


class ListEditAnexosViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.est1 = Establecimiento.objects.create(nombre="Establecimiento 1")
        self.est2 = Establecimiento.objects.create(nombre="Establecimiento 2")

        self.rol = RolOrganizacional.objects.create(nombre="Analista")
        self.depto1 = UnidadOrganizacional.objects.create(nombre="Depto 1", establecimiento=self.est1,
                                                          es_departamento=True)
        self.subdepto1 = UnidadOrganizacional.objects.create(nombre="SubDepto 1", establecimiento=self.est1,
                                                             padre=self.depto1)
        self.depto2 = UnidadOrganizacional.objects.create(nombre="Depto 2", establecimiento=self.est1,
                                                          es_departamento=True)
        self.depto3 = UnidadOrganizacional.objects.create(nombre="Depto 3", establecimiento=self.est2,
                                                          es_departamento=True)

        self.user_editor = User.objects.create_user(username="editor", password="password", establecimiento=self.est1)
        self.perfil = PerfilAgenda.objects.create(usuario=self.user_editor, editor=True)
        self.perfil.unidad_organizacional.add(self.depto1)

        self.anexo1 = Anexo.objects.create(
            anexo="111111",
            nombre_anexo="Anexo 1",
            establecimiento=self.est1,
            unidad_organizacional=self.depto1
        )
        self.anexo_child = Anexo.objects.create(
            anexo="111112",
            nombre_anexo="Anexo Subunidad",
            establecimiento=self.est1,
            unidad_organizacional=self.subdepto1
        )
        self.funcionario = Funcionario.objects.create(
            rut="11111111-1",
            nombres="Pedro",
            apellidos="Gonzales",
            email="pedro@sag.gob.cl",
            cargo="Analista TI",
            rol_organizacional=self.rol,
            unidad_organizacional=self.depto1,
            establecimiento=self.est1,
        )
        self.anexo_func = Anexo.objects.create(
            anexo="111113",
            nombre_anexo="Pedro Gonzales",
            establecimiento=self.est1,
            funcionario=self.funcionario,
        )
        self.anexo2 = Anexo.objects.create(
            anexo="222222",
            nombre_anexo="Anexo 2",
            establecimiento=self.est1,
            unidad_organizacional=self.depto2
        )
        self.anexo3 = Anexo.objects.create(
            anexo="333333",
            nombre_anexo="Anexo 3",
            establecimiento=self.est2,
            unidad_organizacional=self.depto3
        )

    def test_redirect_unauthenticated(self):
        response = self.client.get(reverse('agenda:list_anexos_edit'))
        self.assertEqual(response.status_code, 302)

    def test_filter_by_user_profile_units_and_establishment(self):
        self.client.login(username="editor", password="password")
        response = self.client.post(
            reverse('agenda:list_anexos_edit'),
            {'action': 'search', 'draw': 1, 'start': 0, 'length': 10}
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data['recordsTotal'], 3)
        anexos_returned = [item['anexo'] for item in json_data['data']]
        self.assertIn("111111", anexos_returned)
        self.assertIn("111112", anexos_returned)
        self.assertIn("111113", anexos_returned)
        self.assertNotIn("222222", anexos_returned)
        self.assertNotIn("333333", anexos_returned)

    def test_search_filter(self):
        self.client.login(username="editor", password="password")
        response = self.client.post(
            reverse('agenda:list_anexos_edit'),
            {'action': 'search', 'draw': 1, 'start': 0, 'length': 10, 'search[value]': 'Subunidad'}
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data['recordsFiltered'], 1)
        self.assertEqual(json_data['data'][0]['anexo'], "111112")
