from django.contrib.auth import get_user_model
from django.test import TestCase

from agenda_telefonica.forms import AnexoSinFuncionarioForm
from agenda_telefonica.models import Anexo
from core.models.establecimientos import Establecimiento
from core.models.funcionario import Funcionario
from core.models.rol_organizacional import RolOrganizacional
from core.models.unidad_organizacional import UnidadOrganizacional

User = get_user_model()


class AnexoSinFuncionarioFormTest(TestCase):
    def setUp(self):
        self.est1 = Establecimiento.objects.create(nombre="Establecimiento 1")
        self.est2 = Establecimiento.objects.create(nombre="Establecimiento 2")

        self.uo1 = UnidadOrganizacional.objects.create(nombre="UO 1", establecimiento=self.est1)
        self.uo2 = UnidadOrganizacional.objects.create(nombre="UO 2", establecimiento=self.est2)

        self.user_est1 = User.objects.create(username="user1", establecimiento=self.est1)
        self.user_sin_est = User.objects.create(username="user2")

    def test_filter_by_user_establecimiento(self):
        form = AnexoSinFuncionarioForm(user=self.user_est1)
        qs = form.fields['unidad_organizacional'].queryset
        self.assertIn(self.uo1, qs)
        self.assertNotIn(self.uo2, qs)

    def test_without_user_establecimiento(self):
        form = AnexoSinFuncionarioForm(user=self.user_sin_est)
        qs = form.fields['unidad_organizacional'].queryset
        self.assertIn(self.uo1, qs)
        self.assertIn(self.uo2, qs)


class AnexoSyncFuncionarioTest(TestCase):
    def setUp(self):
        self.est = Establecimiento.objects.create(nombre="Hospital Base")
        self.rol = RolOrganizacional.objects.create(nombre="Jefe")
        self.uo = UnidadOrganizacional.objects.create(nombre="Informatica", establecimiento=self.est)
        self.funcionario = Funcionario.objects.create(
            rut="12345678-9",
            nombres="Juan Carlos",
            apellidos="Perez Gomez",
            email="juan.perez@sag.gob.cl",
            cargo="Jefe de TI",
            rol_organizacional=self.rol,
            unidad_organizacional=self.uo,
            establecimiento=self.est,
        )

    def test_anexo_sync_on_save(self):
        anexo = Anexo.objects.create(
            anexo="123456",
            establecimiento=self.est,
            funcionario=self.funcionario,
        )
        self.assertEqual(anexo.nombre_anexo, "Juan Carlos Perez Gomez")
        self.assertEqual(anexo.email, "juan.perez@sag.gob.cl")
        self.assertEqual(anexo.rol_organizacional, self.rol)
        self.assertEqual(anexo.encargado_de, "Jefe de TI")
        self.assertEqual(anexo.unidad_organizacional, self.uo)

    def test_anexo_sin_funcionario_keeps_manual_values(self):
        anexo = Anexo.objects.create(
            anexo="654321",
            establecimiento=self.est,
            nombre_anexo="Mesa de Ayuda",
            email="soporte@sag.gob.cl",
            encargado_de="Atencion",
            rol_organizacional=self.rol,
            unidad_organizacional=self.uo,
        )
        self.assertEqual(anexo.nombre_anexo, "Mesa de Ayuda")
        self.assertEqual(anexo.email, "soporte@sag.gob.cl")
        self.assertEqual(anexo.rol_organizacional, self.rol)
        self.assertEqual(anexo.encargado_de, "Atencion")
        self.assertEqual(anexo.unidad_organizacional, self.uo)
