from django.test import TestCase, RequestFactory
from django.urls import reverse

from core.models.establecimientos import Establecimiento
from core.models.usuarios import User
from core.standard.views import StandardBaseView, StandardListView, StandardDeleteView


class DummyModel:
    class _Meta:
        verbose_name = 'Dummy'
        verbose_name_plural = 'Dummies'

    _meta = _Meta()
    pk = 1
    id = 1


class StandardViewURLTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.establecimiento = Establecimiento.objects.create(
            nombre="Establecimiento Test",
            alias="ETest",
            region="Coquimbo"
        )
        self.user = User.objects.create_user(
            username="testuser",
            password="password123",
            establecimiento=self.establecimiento,
            is_staff=True,
            is_superuser=True
        )

    def test_standard_base_view_with_none_urls(self):
        view = StandardBaseView()
        self.assertIsNone(view.list_url_name)
        self.assertIsNone(view.create_url_name)
        self.assertIsNone(view.update_url_name)
        self.assertIsNone(view.delete_url_name)
        self.assertIsNone(view.detail_url_name)

        self.assertEqual(view.get_list_url(), '#')
        self.assertEqual(view.get_create_url(), '#')
        self.assertEqual(view.get_update_url(), '#')
        self.assertEqual(view.get_update_url(DummyModel()), '#')
        self.assertEqual(view.get_delete_url(), '#')
        self.assertEqual(view.get_delete_url(DummyModel()), '#')
        self.assertEqual(view.get_detail_url(), '#')
        self.assertEqual(view.get_detail_url(DummyModel()), '#')

    def test_standard_base_view_with_invalid_urls(self):
        view = StandardBaseView()
        view.list_url_name = 'route_does_not_exist_at_all'
        view.create_url_name = 'route_does_not_exist_at_all'
        view.update_url_name = 'route_does_not_exist_at_all'
        view.delete_url_name = 'route_does_not_exist_at_all'
        view.detail_url_name = 'route_does_not_exist_at_all'

        self.assertEqual(view.get_list_url(), '#')
        self.assertEqual(view.get_create_url(), '#')
        self.assertEqual(view.get_update_url(), '#')
        self.assertEqual(view.get_update_url(DummyModel()), '#')
        self.assertEqual(view.get_delete_url(), '#')
        self.assertEqual(view.get_delete_url(DummyModel()), '#')
        self.assertEqual(view.get_detail_url(), '#')
        self.assertEqual(view.get_detail_url(DummyModel()), '#')

    def test_standard_base_view_with_valid_urls(self):
        view = StandardBaseView()
        view.list_url_name = 'core:correo_list'
        view.create_url_name = 'core:correo_create'
        view.update_url_name = 'core:correo_update'
        view.delete_url_name = 'core:correo_delete'

        self.assertEqual(view.get_list_url(), reverse('core:correo_list'))
        self.assertEqual(view.get_create_url(), reverse('core:correo_create'))
        self.assertEqual(view.get_update_url(DummyModel()), reverse('core:correo_update', args=[1]))
        self.assertEqual(view.get_delete_url(DummyModel()), reverse('core:correo_delete', args=[1]))

    def test_standard_list_view_context_data(self):
        class TestListView(StandardListView):
            model = Establecimiento
            list_url_name = 'core:establecimiento_list'
            create_url_name = 'core:establecimiento_create'
            update_url_name = 'core:establecimiento_update'
            delete_url_name = 'core:establecimiento_delete'

        view = TestListView()
        request = self.factory.get('/?q=test')
        request.user = self.user
        view.setup(request)
        view.object_list = view.get_queryset()

        context = view.get_context_data()
        self.assertEqual(context['list_url_name'], 'core:establecimiento_list')
        self.assertEqual(context['create_url_name'], 'core:establecimiento_create')
        self.assertEqual(context['update_url_name'], 'core:establecimiento_update')
        self.assertEqual(context['delete_url_name'], 'core:establecimiento_delete')
        self.assertEqual(context['list_url'], reverse('core:establecimiento_list'))
        self.assertEqual(context['create_url'], reverse('core:establecimiento_create'))
        self.assertEqual(context['q'], 'test')

    def test_standard_delete_view_context_data_and_get_success_url(self):
        class TestDeleteView(StandardDeleteView):
            model = Establecimiento
            list_url_name = 'core:establecimiento_list'

        view = TestDeleteView()
        request = self.factory.get('/')
        request.user = self.user
        view.setup(request)
        view.object = self.establecimiento

        context = view.get_context_data()
        self.assertEqual(context['action'], 'delete')
        self.assertEqual(view.get_success_url(), reverse('core:establecimiento_list'))

    def test_standard_delete_view_soft_delete(self):
        class TestSoftDeleteView(StandardDeleteView):
            model = Establecimiento
            list_url_name = 'core:establecimiento_list'

        view = TestSoftDeleteView()
        request = self.factory.post('/')
        request.user = self.user
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))

        view.setup(request, pk=self.establecimiento.pk)
        view.object = self.establecimiento
        response = view.delete(request, pk=self.establecimiento.pk)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('core:establecimiento_list'))
        self.establecimiento.refresh_from_db()
        self.assertFalse(self.establecimiento.is_active)


class LoginViewTests(TestCase):
    def setUp(self):
        self.establecimiento = Establecimiento.objects.create(
            nombre="Hospital Base Test",
            alias="HBT",
            region="Metropolitana"
        )
        self.user_personal = User.objects.create_user(
            username="11.111.111-1",
            password="Password123!",
            first_name="Juan",
            last_name="Perez",
            establecimiento=self.establecimiento
        )
        self.user_depto = User.objects.create_user(
            username="TI_SOPORTE",
            password="DeptoPassword123!",
            first_name="Soporte",
            last_name="TI",
            establecimiento=self.establecimiento
        )

    def test_login_get_shows_tabs_and_forms(self):
        url = reverse('usuarios:login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base_login.html')
        self.assertContains(response, 'id="personal-tab"')
        self.assertContains(response, 'id="depto-tab"')
        self.assertContains(response, 'name="tipo_acceso" value="PERSONAL"')
        self.assertContains(response, 'name="tipo_acceso" value="DEPARTAMENTO"')
        self.assertContains(response, 'name="alias"')

    def test_login_personal_exitoso(self):
        url = reverse('usuarios:login')
        response = self.client.post(url, {
            'tipo_acceso': 'PERSONAL',
            'username': '11.111.111-1',
            'password': 'Password123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('intranet:index'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user_personal.pk)

    def test_login_departamento_exitoso(self):
        url = reverse('usuarios:login')
        response = self.client.post(url, {
            'tipo_acceso': 'DEPARTAMENTO',
            'alias': 'ti_soporte',
            'password': 'DeptoPassword123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('intranet:index'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user_depto.pk)

    def test_login_personal_fallido(self):
        url = reverse('usuarios:login')
        response = self.client.post(url, {
            'tipo_acceso': 'PERSONAL',
            'username': '11.111.111-1',
            'password': 'WrongPassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Credenciales invalidas')

    def test_login_departamento_fallido(self):
        url = reverse('usuarios:login')
        response = self.client.post(url, {
            'tipo_acceso': 'DEPARTAMENTO',
            'alias': 'ti_soporte',
            'password': 'WrongPassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Credenciales invalidas')
        self.assertEqual(response.context['tipo_acceso'], 'DEPARTAMENTO')
