from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from core.models.establecimientos import Establecimiento
from core.models.funcionario import Funcionario
from core.models.unidad_organizacional import UnidadOrganizacional
from core.models.usuarios import User
from solicitud_vpn.forms import (
    BeneficiarioVPNFormSet,
    SolicitudAccesoFormSet,
)
from solicitud_vpn.models import SolicitudVPN, BeneficiarioVPN, AccesoVPN, PerfilVPN
from solicitud_vpn.permissions import user_is_vpn_gestor
from solicitud_vpn.utils import obtener_departamento_principal, obtener_datos_tecnico_solicitante


class SolicitudVPNModelTests(TestCase):
    def setUp(self):
        self.establecimiento = Establecimiento.objects.create(
            nombre="Hospital Arauco",
            alias="HARAUCO",
            region="Biobío"
        )
        self.depto_raiz = UnidadOrganizacional.objects.create(
            nombre="Dirección Hospital",
            establecimiento=self.establecimiento,
            es_departamento=False
        )
        self.depto_principal = UnidadOrganizacional.objects.create(
            nombre="Departamento de Tecnologías de Información",
            establecimiento=self.establecimiento,
            padre=self.depto_raiz,
            es_departamento=True
        )
        self.seccion = UnidadOrganizacional.objects.create(
            nombre="Sección de Redes y Telecomunicaciones",
            establecimiento=self.establecimiento,
            padre=self.depto_principal,
            es_departamento=False
        )
        self.user = User.objects.create_user(
            username="informatico_arauco",
            password="password123",
            first_name="Carlos",
            last_name="Santana",
            email="csantana@ssarauco.cl",
            establecimiento=self.establecimiento
        )
        self.funcionario = Funcionario.objects.create(
            rut="12.345.678-9",
            nombres="Carlos",
            apellidos="Santana",
            nombre="Carlos Santana",
            cargo="Encargado TIC",
            email="csantana@ssarauco.cl",
            establecimiento=self.establecimiento,
            unidad_organizacional=self.seccion
        )
        self.user.funcionario = self.funcionario
        self.user.save()

    def test_obtener_departamento_principal_jerarquia(self):
        depto_encontrado = obtener_departamento_principal(self.seccion)
        self.assertEqual(depto_encontrado.pk, self.depto_principal.pk)
        self.assertEqual(depto_encontrado.nombre, "Departamento de Tecnologías de Información")

    def test_obtener_datos_tecnico_solicitante(self):
        datos = obtener_datos_tecnico_solicitante(self.user)
        self.assertEqual(datos['nombre_completo'], "Carlos Santana")
        self.assertEqual(datos['rut'], "12.345.678-9")
        self.assertEqual(datos['establecimiento'], "Hospital Arauco")
        self.assertEqual(datos['cargo'], "Encargado TIC")
        self.assertEqual(datos['email'], "csantana@ssarauco.cl")

    def test_creacion_solicitud_vpn_folio_automatico(self):
        solicitud = SolicitudVPN.objects.create(
            establecimiento=self.establecimiento,
            departamento_solicitante=self.depto_principal,
            usuario_solicitante=self.user,
            accion="CREAR",
            tecnico_nombre="Carlos Santana",
            tecnico_rut="12.345.678-9",
            tecnico_establecimiento="Hospital Arauco",
            tecnico_cargo="Encargado TIC",
            tecnico_email="csantana@ssarauco.cl",
            tecnico_fecha=timezone.now().date(),
            es_proveedor=False,
            grupo_vpn="VPN-HARAUCO",
            timeout_vpn="1 hora",
            observacion="Acceso para personal médico"
        )
        self.assertTrue(solicitud.numero_solicitud.startswith("VPN-"))
        self.assertIn("HARAUCO", solicitud.numero_solicitud)
        self.assertEqual(solicitud.estado, "PENDIENTE")
        self.assertEqual(solicitud.departamento_nombre, str(self.depto_principal))

    def test_snapshot_beneficiario_y_accesos_m2m(self):
        solicitud = SolicitudVPN.objects.create(
            establecimiento=self.establecimiento,
            departamento_solicitante=self.depto_principal,
            usuario_solicitante=self.user,
            accion="CREAR",
            tecnico_nombre="Carlos Santana",
            tecnico_rut="12.345.678-9",
            tecnico_email="csantana@ssarauco.cl"
        )

        func_ben = Funcionario.objects.create(
            rut="18.999.888-7",
            nombres="Maria",
            apellidos="Gonzalez",
            nombre="Maria Gonzalez",
            cargo="Médico Urgenciólogo",
            email="mgonzalez@ssarauco.cl",
            establecimiento=self.establecimiento,
            unidad_organizacional=self.depto_principal
        )

        beneficiario = BeneficiarioVPN.objects.create(
            solicitud=solicitud,
            funcionario=func_ben
        )

        self.assertEqual(beneficiario.rut, "18.999.888-7")
        self.assertEqual(beneficiario.nombre_completo, "MARIA GONZALEZ")
        self.assertEqual(beneficiario.cargo, "Médico Urgenciólogo")
        self.assertEqual(beneficiario.establecimiento, "Hospital Arauco")
        self.assertEqual(beneficiario.email, "mgonzalez@ssarauco.cl")

        acc1 = AccesoVPN.objects.create(
            plataforma="Sistema Trackcare",
            ip="10.8.85.25"
        )
        acc2 = AccesoVPN.objects.create(
            plataforma="Red Servidores MINSAL",
            ip="10.8.85.0/24"
        )

        solicitud.accesos.add(acc1, acc2)

        self.assertEqual(solicitud.total_beneficiarios, 1)
        self.assertEqual(solicitud.total_accesos, 2)
        self.assertIn(acc1, solicitud.accesos.all())
        self.assertIn(acc2, solicitud.accesos.all())


class SolicitudVPNFormSetTests(TestCase):
    def setUp(self):
        self.acc1 = AccesoVPN.objects.create(plataforma="Sistema A", ip="10.8.1.1")
        self.acc2 = AccesoVPN.objects.create(plataforma="Sistema B", ip="10.8.1.2")

    def test_solicitud_acceso_formset_duplicate_validation(self):
        # Intentar pasar el mismo acceso duplicado en el formset
        data = {
            'accesos-TOTAL_FORMS': '2',
            'accesos-INITIAL_FORMS': '0',
            'accesos-MIN_NUM_FORMS': '0',
            'accesos-MAX_NUM_FORMS': '1000',
            'accesos-0-acceso': str(self.acc1.id),
            'accesos-1-acceso': str(self.acc1.id),  # Duplicado
        }
        formset = SolicitudAccesoFormSet(data, prefix='accesos')
        self.assertFalse(formset.is_valid())
        self.assertTrue(any('ha sido seleccionado más de una vez' in err for err in formset.non_form_errors()))

    def test_solicitud_acceso_formset_valid_distinct_accesos(self):
        data = {
            'accesos-TOTAL_FORMS': '2',
            'accesos-INITIAL_FORMS': '0',
            'accesos-MIN_NUM_FORMS': '0',
            'accesos-MAX_NUM_FORMS': '1000',
            'accesos-0-acceso': str(self.acc1.id),
            'accesos-1-acceso': str(self.acc2.id),
        }
        formset = SolicitudAccesoFormSet(data, prefix='accesos')
        self.assertTrue(formset.is_valid())

    def test_beneficiario_formset_requires_at_least_one(self):
        solicitud = SolicitudVPN()
        data = {
            'beneficiarios-TOTAL_FORMS': '1',
            'beneficiarios-INITIAL_FORMS': '0',
            'beneficiarios-MIN_NUM_FORMS': '0',
            'beneficiarios-MAX_NUM_FORMS': '1000',
            'beneficiarios-0-rut': '',
            'beneficiarios-0-nombres': '',
        }
        formset = BeneficiarioVPNFormSet(data, instance=solicitud, prefix='beneficiarios')
        self.assertFalse(formset.is_valid())


class SolicitudVPNPermissionsTests(TestCase):
    def setUp(self):
        self.est = Establecimiento.objects.create(nombre="Hospital Curanilahue", alias="HCUR")
        self.user_regular = User.objects.create_user(
            username="usuario_regular", password="password123", first_name="Juan", last_name="Perez"
        )
        self.user_tic = User.objects.create_user(
            username="usuario_tic", password="password123", first_name="Ana", last_name="Rios"
        )
        self.user_admin = User.objects.create_superuser(
            username="admin_vpn", password="password123", email="admin@ssarauco.cl"
        )

        PerfilVPN.objects.create(
            usuario=self.user_tic,
            bandeja_vpn=True,
            nombre_completo="Ana Rios",
            rut="15.111.222-3",
            establecimiento="Hospital Curanilahue",
            cargo="Referente TIC",
            email="arios@ssarauco.cl"
        )

    def test_permissions_checker(self):
        self.assertFalse(user_is_vpn_gestor(self.user_regular))
        self.assertTrue(user_is_vpn_gestor(self.user_tic))
        self.assertTrue(user_is_vpn_gestor(self.user_admin))


class SolicitudVPNViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.est_arauco = Establecimiento.objects.create(nombre="Hospital Arauco", alias="HARAUCO")
        self.est_canete = Establecimiento.objects.create(nombre="Hospital Cañete", alias="HCANETE")
        self.est_lebu = Establecimiento.objects.create(nombre="Hospital Lebu", alias="HLEBU")
        self.depto = UnidadOrganizacional.objects.create(
            nombre="Informática", establecimiento=self.est_arauco, es_departamento=True
        )

        self.user_solicitante = User.objects.create_user(
            username="solicitante_arauco",
            password="password123",
            first_name="Esteban",
            last_name="Dido",
            email="edido@ssarauco.cl",
            establecimiento=self.est_arauco
        )
        self.func_sol = Funcionario.objects.create(
            rut="14.555.666-7",
            nombres="Esteban",
            apellidos="Dido",
            nombre="Esteban Dido",
            cargo="Técnico Informático",
            email="edido@ssarauco.cl",
            establecimiento=self.est_arauco,
            unidad_organizacional=self.depto
        )
        self.user_solicitante.funcionario = self.func_sol
        self.user_solicitante.save()

        self.user_tic = User.objects.create_user(
            username="gestor_tic",
            password="password123",
            first_name="Marta",
            last_name="Sanchez",
            email="msanchez@ssarauco.cl",
            establecimiento=self.est_arauco
        )
        PerfilVPN.objects.create(
            usuario=self.user_tic,
            bandeja_vpn=True,
            nombre_completo="Marta Sanchez",
            rut="11.222.333-4",
            establecimiento="Dirección de Servicio",
            cargo="Encargada Redes y Seguridad TIC",
            email="msanchez@ssarauco.cl"
        )

        self.acc1 = AccesoVPN.objects.create(plataforma="Sistema Trackcare", ip="10.8.85.25")
        self.acc2 = AccesoVPN.objects.create(plataforma="Intranet Arauco", ip="10.8.85.50")

    def test_mis_solicitudes_view(self):
        self.client.login(username="solicitante_arauco", password="password123")
        response = self.client.get(reverse('solicitud_vpn:mis_solicitudes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mis Solicitudes de Acceso VPN")
        self.assertContains(response, "Generar requerimiento")

    def test_form_solicitud_view_renderizado_botones_y_scripts(self):
        self.client.login(username="solicitante_arauco", password="password123")
        response = self.client.get(reverse('solicitud_vpn:crear'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Generar Requerimiento de Acceso VPN")
        self.assertContains(response, "btn-agregar-beneficiario")
        self.assertContains(response, "btn-agregar-acceso")
        self.assertContains(response, "btn-guardar-borrador")
        self.assertContains(response, "btn-revisar-enviar")

    def test_creacion_solicitud_con_formsets_exito(self):
        self.client.login(username="solicitante_arauco", password="password123")

        post_data = {
            'departamento_solicitante': self.depto.id,
            'accion': 'CREAR',
            'grupo_vpn': 'VPN-HARAUCO-URGENCIA',
            'timeout_vpn': '1 hora',
            'observacion': 'Requerimiento para médicos y paramédicos de urgencia',
            'tecnico_nombre': 'Esteban Dido',
            'tecnico_rut': '14.555.666-7',
            'tecnico_establecimiento': 'Hospital Arauco',
            'tecnico_cargo': 'Técnico Informático',
            'tecnico_telefono': '+56 9 1111 2222',
            'tecnico_email': 'edido@ssarauco.cl',
            'tecnico_fecha': '2026-10-01',
            'es_proveedor': False,
            'guardar_borrador': '0',

            # Beneficiarios FormSet
            'beneficiarios-TOTAL_FORMS': '2',
            'beneficiarios-INITIAL_FORMS': '0',
            'beneficiarios-MIN_NUM_FORMS': '0',
            'beneficiarios-MAX_NUM_FORMS': '1000',
            'beneficiarios-0-rut': '16.777.888-9',
            'beneficiarios-0-nombres': 'Claudio',
            'beneficiarios-0-apellidos': 'Bravos',
            'beneficiarios-0-establecimiento': 'Hospital Arauco',
            'beneficiarios-0-cargo': 'Enfermero',
            'beneficiarios-0-telefono': '+56 9 1234 5678',
            'beneficiarios-0-email': 'cbravos@ssarauco.cl',
            'beneficiarios-1-rut': '17.123.456-7',
            'beneficiarios-1-nombres': 'Alexis',
            'beneficiarios-1-apellidos': 'Sanches',
            'beneficiarios-1-establecimiento': 'Hospital Arauco',
            'beneficiarios-1-cargo': 'Kinesiólogo',
            'beneficiarios-1-telefono': '+56 9 8765 4321',
            'beneficiarios-1-email': 'asanches@ssarauco.cl',

            # Accesos FormSet
            'accesos-TOTAL_FORMS': '2',
            'accesos-INITIAL_FORMS': '0',
            'accesos-MIN_NUM_FORMS': '0',
            'accesos-MAX_NUM_FORMS': '1000',
            'accesos-0-acceso': str(self.acc1.id),
            'accesos-1-acceso': str(self.acc2.id),
        }

        response = self.client.post(reverse('solicitud_vpn:crear'), post_data)
        self.assertEqual(response.status_code, 302)

        solicitud = SolicitudVPN.objects.filter(usuario_solicitante=self.user_solicitante).first()
        self.assertIsNotNone(solicitud)
        self.assertEqual(solicitud.estado, 'PENDIENTE')
        self.assertEqual(solicitud.total_beneficiarios, 2)
        self.assertEqual(solicitud.total_accesos, 2)
        self.assertIn(self.acc1, solicitud.accesos.all())
        self.assertIn(self.acc2, solicitud.accesos.all())

    def test_creacion_solicitud_con_acceso_duplicado_falla(self):
        self.client.login(username="solicitante_arauco", password="password123")

        post_data = {
            'departamento_solicitante': self.depto.id,
            'accion': 'CREAR',
            'tecnico_nombre': 'Esteban Dido',
            'tecnico_rut': '14.555.666-7',
            'tecnico_establecimiento': 'Hospital Arauco',
            'tecnico_email': 'edido@ssarauco.cl',
            'tecnico_fecha': '2026-10-01',

            # Beneficiarios FormSet
            'beneficiarios-TOTAL_FORMS': '1',
            'beneficiarios-INITIAL_FORMS': '0',
            'beneficiarios-MIN_NUM_FORMS': '0',
            'beneficiarios-MAX_NUM_FORMS': '1000',
            'beneficiarios-0-rut': '16.777.888-9',
            'beneficiarios-0-nombres': 'Claudio',

            # Accesos FormSet con duplicados
            'accesos-TOTAL_FORMS': '2',
            'accesos-INITIAL_FORMS': '0',
            'accesos-MIN_NUM_FORMS': '0',
            'accesos-MAX_NUM_FORMS': '1000',
            'accesos-0-acceso': str(self.acc1.id),
            'accesos-1-acceso': str(self.acc1.id),
        }

        response = self.client.post(reverse('solicitud_vpn:crear'), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ha sido seleccionado más de una vez')
        self.assertEqual(SolicitudVPN.objects.count(), 0)

    def test_guardar_solicitud_como_borrador(self):
        self.client.login(username="solicitante_arauco", password="password123")

        post_data = {
            'departamento_solicitante': self.depto.id,
            'accion': 'ACTUALIZAR',
            'grupo_vpn': 'VPN-TEMP',
            'timeout_vpn': '30 min',
            'tecnico_nombre': 'Esteban Dido',
            'tecnico_rut': '14.555.666-7',
            'tecnico_establecimiento': 'Hospital Arauco',
            'tecnico_email': 'edido@ssarauco.cl',
            'tecnico_fecha': '2026-10-01',
            'guardar_borrador': '1',

            'beneficiarios-TOTAL_FORMS': '1',
            'beneficiarios-INITIAL_FORMS': '0',
            'beneficiarios-MIN_NUM_FORMS': '0',
            'beneficiarios-MAX_NUM_FORMS': '1000',
            'beneficiarios-0-rut': '19.444.555-6',
            'beneficiarios-0-nombres': 'Borrador',
            'beneficiarios-0-apellidos': 'User',
            'beneficiarios-0-establecimiento': 'Hospital Arauco',

            'accesos-TOTAL_FORMS': '0',
            'accesos-INITIAL_FORMS': '0',
            'accesos-MIN_NUM_FORMS': '0',
            'accesos-MAX_NUM_FORMS': '1000',
        }

        response = self.client.post(reverse('solicitud_vpn:crear'), post_data)
        self.assertEqual(response.status_code, 302)

        solicitud = SolicitudVPN.objects.filter(estado='BORRADOR').first()
        self.assertIsNotNone(solicitud)
        self.assertEqual(solicitud.accion, 'ACTUALIZAR')

    def test_validacion_sin_beneficiarios_retorna_error(self):
        self.client.login(username="solicitante_arauco", password="password123")

        post_data = {
            'departamento_solicitante': self.depto.id,
            'accion': 'ELIMINAR',
            'tecnico_nombre': 'Esteban Dido',
            'tecnico_rut': '14.555.666-7',
            'tecnico_establecimiento': 'Hospital Arauco',
            'tecnico_email': 'edido@ssarauco.cl',
            'tecnico_fecha': '2026-10-01',
            'guardar_borrador': '0',

            'beneficiarios-TOTAL_FORMS': '0',
            'beneficiarios-INITIAL_FORMS': '0',
            'beneficiarios-MIN_NUM_FORMS': '0',
            'beneficiarios-MAX_NUM_FORMS': '1000',

            'accesos-TOTAL_FORMS': '0',
            'accesos-INITIAL_FORMS': '0',
            'accesos-MIN_NUM_FORMS': '0',
            'accesos-MAX_NUM_FORMS': '1000',
        }

        response = self.client.post(reverse('solicitud_vpn:crear'), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Debe ingresar al menos un beneficiario')

    def test_bandeja_tic_view_and_permissions(self):
        self.client.login(username="solicitante_arauco", password="password123")
        response = self.client.get(reverse('solicitud_vpn:bandeja_tic'))
        self.assertEqual(response.status_code, 302)

        self.client.login(username="gestor_tic", password="password123")
        response = self.client.get(reverse('solicitud_vpn:bandeja_tic'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bandeja de Gestión VPN")

    def test_bandeja_tic_filtros(self):
        SolicitudVPN.objects.create(
            establecimiento=self.est_arauco,
            usuario_solicitante=self.user_solicitante,
            accion="CREAR",
            estado="PENDIENTE",
            tecnico_nombre="Esteban Dido",
            tecnico_rut="14.555.666-7",
            tecnico_email="edido@ssarauco.cl",
            numero_solicitud="VPN-2026-HARAUCO-00001"
        )
        SolicitudVPN.objects.create(
            establecimiento=self.est_canete,
            usuario_solicitante=self.user_solicitante,
            accion="ELIMINAR",
            estado="COMPLETADO",
            tecnico_nombre="Esteban Dido",
            tecnico_rut="14.555.666-7",
            tecnico_email="edido@ssarauco.cl",
            numero_solicitud="VPN-2026-HCANETE-00001"
        )

        self.client.login(username="gestor_tic", password="password123")

        # Filtrar por establecimiento Cañete
        response = self.client.get(reverse('solicitud_vpn:bandeja_tic'), {'establecimiento': self.est_canete.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "VPN-2026-HCANETE-00001")
        self.assertNotContains(response, "VPN-2026-HARAUCO-00001")

        # Filtrar por estado PENDIENTE
        response_pend = self.client.get(reverse('solicitud_vpn:bandeja_tic'), {'estado': 'PENDIENTE'})
        self.assertEqual(response_pend.status_code, 200)
        self.assertContains(response_pend, "VPN-2026-HARAUCO-00001")
        self.assertNotContains(response_pend, "VPN-2026-HCANETE-00001")

    def test_detalle_solicitud_y_cambio_estado_tic(self):
        solicitud = SolicitudVPN.objects.create(
            establecimiento=self.est_arauco,
            departamento_solicitante=self.depto,
            usuario_solicitante=self.user_solicitante,
            accion="CREAR",
            tecnico_nombre="Esteban Dido",
            tecnico_rut="14.555.666-7",
            tecnico_establecimiento="Hospital Arauco",
            tecnico_email="edido@ssarauco.cl",
            estado="PENDIENTE"
        )
        BeneficiarioVPN.objects.create(
            solicitud=solicitud,
            rut="16.777.888-9",
            nombres="Claudio",
            apellidos="Bravos",
            nombre_completo="Claudio Bravos",
            establecimiento="Hospital Arauco",
            cargo="Enfermero"
        )
        solicitud.accesos.add(self.acc1)

        self.client.login(username="gestor_tic", password="password123")
        response = self.client.get(reverse('solicitud_vpn:detalle', kwargs={'pk': solicitud.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CLAUDIO BRAVOS")
        self.assertContains(response, "10.8.85.25")
        self.assertContains(response, "Copiar Todo para eConecta")

        # Cambiar estado a ENVIADO_ECONECTA
        response_post = self.client.post(
            reverse('solicitud_vpn:cambiar_estado', kwargs={'pk': solicitud.pk}),
            {
                'estado': 'ENVIADO_ECONECTA',
                'ticket_econecta': 'REQ-2026-99881',
                'observacion_revision': 'Solicitud tramitada con mesa de ayuda MINSAL eConecta'
            }
        )
        self.assertEqual(response_post.status_code, 302)

        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, 'ENVIADO_ECONECTA')
        self.assertEqual(solicitud.ticket_econecta, 'REQ-2026-99881')
        self.assertIsNotNone(solicitud.fecha_envio_econecta)

        # Cambiar estado a COMPLETADO
        response_post2 = self.client.post(
            reverse('solicitud_vpn:cambiar_estado', kwargs={'pk': solicitud.pk}),
            {
                'estado': 'COMPLETADO',
                'ticket_econecta': 'REQ-2026-99881',
                'observacion_revision': 'Habilitación finalizada y comprobada'
            }
        )
        self.assertEqual(response_post2.status_code, 302)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, 'COMPLETADO')
        self.assertIsNotNone(solicitud.fecha_finalizacion)

    def test_perfil_vpn_view(self):
        self.client.login(username="solicitante_arauco", password="password123")
        response = self.client.get(reverse('solicitud_vpn:perfil'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mi Perfil de Referente VPN")

        post_data = {
            'nombre_completo': 'Esteban Dido Actualizado',
            'rut': '14.555.666-7',
            'establecimiento': 'Hospital Arauco',
            'cargo': 'Jefe TIC',
            'telefono': '+56 9 9999 8888',
            'email': 'edido@ssarauco.cl',
        }
        response = self.client.post(reverse('solicitud_vpn:perfil'), post_data)
        self.assertEqual(response.status_code, 302)

        perfil = PerfilVPN.objects.get(usuario=self.user_solicitante)
        self.assertEqual(perfil.nombre_completo, 'ESTEBAN DIDO ACTUALIZADO')
        self.assertEqual(perfil.cargo, 'Jefe TIC')

    def test_api_funcionario_json(self):
        self.client.login(username="solicitante_arauco", password="password123")
        response = self.client.get(reverse('solicitud_vpn:api_funcionario', kwargs={'pk': self.func_sol.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['data']['rut'], '14.555.666-7')
        self.assertEqual(data['data']['nombres'], 'Esteban')
        self.assertEqual(data['data']['apellidos'], 'Dido')
        self.assertEqual(data['data']['establecimiento'], 'Hospital Arauco')
        self.assertEqual(data['data']['cargo'], 'Técnico Informático')
        self.assertEqual(data['data']['email'], 'edido@ssarauco.cl')

    def test_fbv_solicitud_marcar_econecta(self):
        solicitud = SolicitudVPN.objects.create(
            establecimiento=self.est_arauco,
            usuario_solicitante=self.user_solicitante,
            accion="CREAR",
            tecnico_nombre="Esteban Dido",
            tecnico_email="edido@ssarauco.cl",
            estado="PENDIENTE"
        )
        self.client.login(username="gestor_tic", password="password123")
        response = self.client.post(
            reverse('solicitud_vpn:marcar_econecta', kwargs={'pk': solicitud.pk}),
            {'ticket_econecta': 'TK-MINSAL-8822'}
        )
        self.assertEqual(response.status_code, 302)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, 'ENVIADO_ECONECTA')
        self.assertEqual(solicitud.ticket_econecta, 'TK-MINSAL-8822')
        self.assertIsNotNone(solicitud.fecha_envio_econecta)

    def test_fbv_solicitud_marcar_completado(self):
        solicitud = SolicitudVPN.objects.create(
            establecimiento=self.est_arauco,
            usuario_solicitante=self.user_solicitante,
            accion="CREAR",
            tecnico_nombre="Esteban Dido",
            tecnico_email="edido@ssarauco.cl",
            estado="ENVIADO_ECONECTA"
        )
        self.client.login(username="gestor_tic", password="password123")
        response = self.client.post(reverse('solicitud_vpn:marcar_completado', kwargs={'pk': solicitud.pk}))
        self.assertEqual(response.status_code, 302)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, 'COMPLETADO')
        self.assertIsNotNone(solicitud.fecha_finalizacion)

    def test_fbv_solicitud_eliminar(self):
        solicitud = SolicitudVPN.objects.create(
            establecimiento=self.est_arauco,
            usuario_solicitante=self.user_solicitante,
            accion="CREAR",
            tecnico_nombre="Esteban Dido",
            tecnico_email="edido@ssarauco.cl",
            estado="PENDIENTE"
        )
        self.client.login(username="gestor_tic", password="password123")
        response = self.client.post(reverse('solicitud_vpn:eliminar', kwargs={'pk': solicitud.pk}))
        self.assertEqual(response.status_code, 302)
        solicitud.refresh_from_db()
        self.assertFalse(solicitud.is_active)

    @patch('core.services.email_service.EmailService.send_email_with_config')
    def test_fbv_solicitud_notificar(self, mock_send_email):
        mock_send_email.return_value = True

        # Crear configuración de correo para el establecimiento del usuario gestor
        from core.models.configuracion_correo import ConfiguracionCorreo
        ConfiguracionCorreo.objects.create(
            establecimiento=self.est_arauco,
            nombre_remitente="TIC Hospital Arauco",
            email_remitente="tic@ssarauco.cl",
            smtp_host="smtp.ssarauco.cl",
            smtp_port=587,
            smtp_tls=True,
            smtp_usuario="tic@ssarauco.cl",
            _smtp_password="password_secret",
            activo=True
        )

        solicitud = SolicitudVPN.objects.create(
            establecimiento=self.est_arauco,
            usuario_solicitante=self.user_solicitante,
            accion="CREAR",
            tecnico_nombre="Esteban Dido",
            tecnico_email="edido@ssarauco.cl",
            estado="COMPLETADO"
        )
        self.client.login(username="gestor_tic", password="password123")
        response = self.client.post(
            reverse('solicitud_vpn:notificar', kwargs={'pk': solicitud.pk}),
            {'mensaje': 'Su solicitud de VPN ya está lista para su uso.'}
        )
        self.assertEqual(response.status_code, 302)
        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        self.assertEqual(kwargs['recipient_list'], ['edido@ssarauco.cl'])
        self.assertEqual(kwargs['template_name'], 'solicitud_vpn/emails/notificacion_solicitante.html')
        self.assertEqual(kwargs['config'].establecimiento, self.est_arauco)

    def test_fbv_permiso_denegado_usuario_comun(self):
        solicitud = SolicitudVPN.objects.create(
            establecimiento=self.est_arauco,
            usuario_solicitante=self.user_solicitante,
            accion="CREAR",
            tecnico_nombre="Esteban Dido",
            tecnico_email="edido@ssarauco.cl",
            estado="PENDIENTE"
        )
        self.client.login(username="solicitante_arauco", password="password123")
        response = self.client.post(reverse('solicitud_vpn:eliminar', kwargs={'pk': solicitud.pk}))
        # Redirige a mis_solicitudes por falta de permiso
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('solicitud_vpn:mis_solicitudes'), response.url)
        solicitud.refresh_from_db()
        self.assertTrue(solicitud.is_active)
