from django.contrib.auth import get_user_model
from django.test import TestCase

from agenda_telefonica.forms import AnexoSinFuncionarioForm
from core.models.establecimientos import Establecimiento
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
