from django.contrib.auth.models import Group
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from core.models.establecimientos import Establecimiento
from core.models.funcionario import Funcionario
from core.models.unidad_organizacional import UnidadOrganizacional
from core.models.usuarios import User
from solicitud_correo.models import SolicitudCorreo, SolicitudCorreoDetalle
from solicitud_correo.permissions import user_is_rrhh, user_is_tic
from soporte.models import PerfilSoporte


class SolicitudCorreoModelTests(TestCase):
    def setUp(self):
        self.establecimiento = Establecimiento.objects.create(
            nombre="Hospital San Pablo",
            alias="HSP",
            region="Coquimbo"
        )
        self.depto = UnidadOrganizacional.objects.create(
            nombre="Departamento de Finanzas",
            establecimiento=self.establecimiento,
            es_departamento=True
        )
        self.user = User.objects.create_user(
            username="solicitante1",
            password="password123",
            first_name="Pedro",
            last_name="Pascal",
            establecimiento=self.establecimiento
        )
        self.funcionario = Funcionario.objects.create(
            rut="11.222.333-4",
            nombres="Maria Jose",
            apellidos="Lopez Lopez",
            cargo="Analista Contable",
            establecimiento=self.establecimiento,
            unidad_organizacional=self.depto
        )

    def test_creacion_solicitud_folio_automatico(self):
        solicitud = SolicitudCorreo.objects.create(
            establecimiento=self.establecimiento,
            departamento_solicitante=self.depto,
            usuario_solicitante=self.user,
            observacion="Solicitud urgente"
        )
        self.assertTrue(solicitud.numero_solicitud.startswith("SOL-"))
        self.assertIn("HSP", solicitud.numero_solicitud)
        self.assertEqual(solicitud.estado, "PENDIENTE_RRHH")
        self.assertEqual(solicitud.departamento_nombre, str(self.depto))

    def test_snapshot_historico_funcionario_en_detalle(self):
        solicitud = SolicitudCorreo.objects.create(
            establecimiento=self.establecimiento,
            departamento_solicitante=self.depto,
            usuario_solicitante=self.user
        )

        detalle = SolicitudCorreoDetalle.objects.create(
            solicitud=solicitud,
            funcionario=self.funcionario
        )

        # Verificar que se copió el snapshot
        self.assertEqual(detalle.rut, "11.222.333-4")
        self.assertEqual(detalle.nombres, "MARIA JOSE")
        self.assertEqual(detalle.apellidos, "LOPEZ LOPEZ")
        self.assertEqual(detalle.cargo, "Analista Contable")
        self.assertEqual(detalle.departamento, str(self.depto))

        # Modificar funcionario original
        self.funcionario.nombres = "Maria Antonieta"
        self.funcionario.cargo = "Jefa de Finanzas"
        self.funcionario.save()

        # Recargar detalle desde la base de datos
        detalle.refresh_from_db()

        # El snapshot histórico NO debe haber cambiado
        self.assertEqual(detalle.nombres, "MARIA JOSE")
        self.assertEqual(detalle.cargo, "Analista Contable")

    def test_actualizar_estado_general_flujo_completo(self):
        solicitud = SolicitudCorreo.objects.create(
            establecimiento=self.establecimiento,
            departamento_solicitante=self.depto,
            usuario_solicitante=self.user
        )

        det1 = SolicitudCorreoDetalle.objects.create(
            solicitud=solicitud,
            rut="1-1",
            nombres="Funcionario 1",
            apellidos="Uno",
            estado="PENDIENTE_RRHH"
        )
        det2 = SolicitudCorreoDetalle.objects.create(
            solicitud=solicitud,
            rut="2-2",
            nombres="Funcionario 2",
            apellidos="Dos",
            estado="PENDIENTE_RRHH"
        )

        # 1. Inicialmente: PENDIENTE_RRHH
        solicitud.actualizar_estado_general()
        self.assertEqual(solicitud.estado, "PENDIENTE_RRHH")

        # 2. Revisión parcial en RR.HH. (uno aprobado, uno pendiente)
        det1.estado = "APROBADO_RRHH"
        det1.save()
        solicitud.actualizar_estado_general()
        self.assertEqual(solicitud.estado, "EN_REVISION_RRHH")

        # 3. Revisión completa en RR.HH. (uno aprobado, uno rechazado) -> Pasa a EN_TIC
        det2.estado = "RECHAZADO_RRHH"
        det2.motivo_rechazo = "No corresponde crear cuenta"
        det2.save()
        solicitud.actualizar_estado_general()
        self.assertEqual(solicitud.estado, "EN_TIC")
        self.assertIsNotNone(solicitud.fecha_envio_tic)

        # 4. TIC crea la cuenta del funcionario aprobado -> Finalizada
        det1.estado = "CREADO"
        det1.correo_creado = "funcionario1@redsalud.gob.cl"
        det1.fecha_creacion = timezone.now()
        det1.save()
        solicitud.actualizar_estado_general()
        self.assertEqual(solicitud.estado, "FINALIZADA")
        self.assertIsNotNone(solicitud.fecha_finalizacion)

    def test_todos_rechazados_finaliza_solicitud(self):
        solicitud = SolicitudCorreo.objects.create(
            establecimiento=self.establecimiento,
            departamento_solicitante=self.depto,
            usuario_solicitante=self.user
        )

        det1 = SolicitudCorreoDetalle.objects.create(
            solicitud=solicitud,
            rut="1-1",
            nombres="Func 1",
            apellidos="Uno",
            estado="RECHAZADO_RRHH",
            motivo_rechazo="Rechazado"
        )
        det2 = SolicitudCorreoDetalle.objects.create(
            solicitud=solicitud,
            rut="2-2",
            nombres="Func 2",
            apellidos="Dos",
            estado="RECHAZADO_RRHH",
            motivo_rechazo="Rechazado"
        )

        solicitud.actualizar_estado_general()
        self.assertEqual(solicitud.estado, "FINALIZADA")

    def test_simple_history_trazabilidad(self):
        solicitud = SolicitudCorreo.objects.create(
            establecimiento=self.establecimiento,
            departamento_solicitante=self.depto,
            usuario_solicitante=self.user,
            estado="PENDIENTE_RRHH"
        )
        detalle = SolicitudCorreoDetalle.objects.create(
            solicitud=solicitud,
            rut="3-3",
            nombres="Func 3",
            apellidos="Tres",
            estado="PENDIENTE_RRHH"
        )

        # Modificaciones
        solicitud.estado = "EN_TIC"
        solicitud.save()

        detalle.estado = "APROBADO_RRHH"
        detalle.save()

        # Validar que history registra los eventos
        self.assertGreaterEqual(solicitud.history.count(), 2)
        self.assertGreaterEqual(detalle.history.count(), 2)


class SolicitudCorreoPermissionsAndViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.establecimiento = Establecimiento.objects.create(
            nombre="Hospital San Pablo",
            alias="HSP",
            region="Coquimbo"
        )
        self.depto_rrhh = UnidadOrganizacional.objects.create(
            nombre="Departamento de Recursos Humanos",
            establecimiento=self.establecimiento,
            es_departamento=True
        )
        self.depto_tic = UnidadOrganizacional.objects.create(
            nombre="Departamento de Informatica y TIC",
            establecimiento=self.establecimiento,
            es_departamento=True
        )
        self.depto_clinico = UnidadOrganizacional.objects.create(
            nombre="Servicio de Medicina",
            establecimiento=self.establecimiento,
            es_departamento=True
        )

        # Usuario Normal (Solicitante)
        self.user_normal = User.objects.create_user(
            username="usuario_normal",
            password="password123",
            first_name="Usuario",
            last_name="Normal",
            establecimiento=self.establecimiento
        )

        # Usuario RR.HH.
        self.user_rrhh = User.objects.create_user(
            username="usuario_rrhh",
            password="password123",
            first_name="Revisor",
            last_name="RRHH",
            establecimiento=self.establecimiento
        )
        grupo_rrhh, _ = Group.objects.get_or_create(name="Recursos Humanos")
        self.user_rrhh.groups.add(grupo_rrhh)

        # Usuario TIC
        self.user_tic = User.objects.create_user(
            username="usuario_tic",
            password="password123",
            first_name="Tecnico",
            last_name="TIC",
            establecimiento=self.establecimiento
        )
        self.perfil_soporte = PerfilSoporte.objects.create(
            usuario=self.user_tic,
            is_active=True
        )

        # Superuser
        self.user_admin = User.objects.create_superuser(
            username="admin_user",
            password="password123",
            email="admin@sag.cl"
        )

        # Funcionario para pruebas
        self.funcionario_ejemplo = Funcionario.objects.create(
            rut="12.345.678-9",
            nombres="Andrea",
            apellidos="Castillo Soto",
            cargo="Enfermera",
            establecimiento=self.establecimiento,
            unidad_organizacional=self.depto_clinico
        )

    def test_helpers_permisos(self):
        self.assertFalse(user_is_rrhh(self.user_normal))
        self.assertFalse(user_is_tic(self.user_normal))

        self.assertTrue(user_is_rrhh(self.user_rrhh))
        self.assertFalse(user_is_tic(self.user_rrhh))

        self.assertTrue(user_is_tic(self.user_tic))
        self.assertFalse(user_is_rrhh(self.user_tic))

        self.assertTrue(user_is_rrhh(self.user_admin))
        self.assertTrue(user_is_tic(self.user_admin))

    def test_usuario_normal_crear_solicitud(self):
        self.client.login(username="usuario_normal", password="password123")
        url_crear = reverse("solicitud_correo:crear")

        # GET form
        response = self.client.get(url_crear)
        self.assertEqual(response.status_code, 200)

        # POST nueva solicitud con 2 funcionarios (1 registrado + 1 manual)
        post_data = {
            'departamento_solicitante': self.depto_clinico.pk,
            'observacion': 'Creación para nuevo personal del servicio',
            'det_funcionario_id[]': [str(self.funcionario_ejemplo.pk), ''],
            'det_rut[]': [self.funcionario_ejemplo.rut, '15.678.901-2'],
            'det_nombres[]': [self.funcionario_ejemplo.nombres, 'Carlos'],
            'det_apellidos[]': [self.funcionario_ejemplo.apellidos, 'Vargas'],
            'det_departamento[]': ['Medicina', 'Medicina'],
            'det_cargo[]': ['Enfermera', 'Tens'],
        }

        response = self.client.post(url_crear, post_data)
        self.assertEqual(response.status_code, 302)

        # Verificar en BD
        solicitud = SolicitudCorreo.objects.filter(usuario_solicitante=self.user_normal).first()
        self.assertIsNotNone(solicitud)
        self.assertEqual(solicitud.estado, "PENDIENTE_RRHH")
        self.assertEqual(solicitud.detalles.count(), 2)

        detalles = list(solicitud.detalles.all())
        self.assertEqual(detalles[0].rut, "12.345.678-9")
        self.assertEqual(detalles[0].estado, "PENDIENTE_RRHH")
        self.assertEqual(detalles[1].rut, "15.678.901-2")
        self.assertEqual(detalles[1].estado, "PENDIENTE_RRHH")

    def test_usuario_normal_no_puede_acceder_a_bandeja_rrhh_o_tic(self):
        self.client.login(username="usuario_normal", password="password123")

        # Intentar acceder a Bandeja RR.HH.
        resp_rrhh = self.client.get(reverse("solicitud_correo:bandeja_rrhh"))
        self.assertEqual(resp_rrhh.status_code, 302)  # Redirigido a mis_solicitudes

        # Intentar acceder a Bandeja TIC
        resp_tic = self.client.get(reverse("solicitud_correo:bandeja_tic"))
        self.assertEqual(resp_tic.status_code, 302)  # Redirigido a mis_solicitudes

    def test_flujo_completo_rrhh_aprobar_y_rechazar(self):
        # 1. Crear solicitud por usuario normal
        solicitud = SolicitudCorreo.objects.create(
            establecimiento=self.establecimiento,
            departamento_solicitante=self.depto_clinico,
            usuario_solicitante=self.user_normal,
            estado="PENDIENTE_RRHH"
        )
        det_aprobar = SolicitudCorreoDetalle.objects.create(
            solicitud=solicitud,
            rut="11.111.111-1",
            nombres="Maria",
            apellidos="Aprobada",
            estado="PENDIENTE_RRHH"
        )
        det_rechazar = SolicitudCorreoDetalle.objects.create(
            solicitud=solicitud,
            rut="22.222.222-2",
            nombres="Jose",
            apellidos="Rechazado",
            estado="PENDIENTE_RRHH"
        )

        # 2. Login como RR.HH.
        self.client.login(username="usuario_rrhh", password="password123")

        # Ver Bandeja RR.HH.
        resp_bandeja = self.client.get(reverse("solicitud_correo:bandeja_rrhh"))
        self.assertEqual(resp_bandeja.status_code, 200)

        # Aprobar det_aprobar
        url_rev_aprob = reverse("solicitud_correo:revisar_detalle_rrhh", args=[det_aprobar.pk])
        resp_aprob = self.client.post(url_rev_aprob, {'accion': 'APROBADO_RRHH'})
        self.assertEqual(resp_aprob.status_code, 302)

        det_aprobar.refresh_from_db()
        self.assertEqual(det_aprobar.estado, "APROBADO_RRHH")
        self.assertEqual(det_aprobar.usuario_rrhh, self.user_rrhh)

        # Rechazar det_rechazar sin motivo debe fallar
        url_rev_rech = reverse("solicitud_correo:revisar_detalle_rrhh", args=[det_rechazar.pk])
        resp_rech_sin_motivo = self.client.post(url_rev_rech, {'accion': 'RECHAZADO_RRHH', 'motivo_rechazo': ''})
        det_rechazar.refresh_from_db()
        self.assertEqual(det_rechazar.estado, "PENDIENTE_RRHH")

        # Rechazar con motivo válido
        resp_rech_con_motivo = self.client.post(url_rev_rech, {
            'accion': 'RECHAZADO_RRHH',
            'motivo_rechazo': 'Funcionario ya cuenta con correo institucional activo'
        })
        self.assertEqual(resp_rech_con_motivo.status_code, 302)

        det_rechazar.refresh_from_db()
        self.assertEqual(det_rechazar.estado, "RECHAZADO_RRHH")
        self.assertEqual(det_rechazar.motivo_rechazo, 'Funcionario ya cuenta con correo institucional activo')

        # Solicitud ahora debe estar en EN_TIC porque se revisaron todos y hay 1 aprobado
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, "EN_TIC")

    def test_flujo_completo_tic_procesar_y_notificar(self):
        # 1. Crear solicitud con funcionario aprobado
        solicitud = SolicitudCorreo.objects.create(
            establecimiento=self.establecimiento,
            departamento_solicitante=self.depto_clinico,
            usuario_solicitante=self.user_normal,
            estado="EN_TIC"
        )
        detalle = SolicitudCorreoDetalle.objects.create(
            solicitud=solicitud,
            rut="11.111.111-1",
            nombres="Maria",
            apellidos="Aprobada",
            estado="APROBADO_RRHH",
            usuario_rrhh=self.user_rrhh
        )

        # 2. Login como TIC
        self.client.login(username="usuario_tic", password="password123")

        # Ver Bandeja TIC
        resp_bandeja_tic = self.client.get(reverse("solicitud_correo:bandeja_tic"))
        self.assertEqual(resp_bandeja_tic.status_code, 200)

        # Registrar Creación Exitosa
        url_proc_tic = reverse("solicitud_correo:procesar_detalle_tic", args=[detalle.pk])
        resp_proc = self.client.post(url_proc_tic, {
            'accion': 'CREADO',
            'correo_creado': 'maria.aprobada@redsalud.gob.cl',
            'referencia_externa': 'REQ-MINSAL-9988',
            'observacion_tic': 'Cuenta creada en Azure AD / Exchange MINSAL'
        })
        self.assertEqual(resp_proc.status_code, 302)

        detalle.refresh_from_db()
        self.assertEqual(detalle.estado, "CREADO")
        self.assertEqual(detalle.correo_creado, "maria.aprobada@redsalud.gob.cl")
        self.assertEqual(detalle.referencia_externa, "REQ-MINSAL-9988")
        self.assertEqual(detalle.tecnico_responsable, self.user_tic)

        # La solicitud debe estar FINALIZADA
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, "FINALIZADA")

        # 3. Notificación al funcionario
        url_notif = reverse("solicitud_correo:notificar_detalle", args=[detalle.pk])
        resp_notif = self.client.post(url_notif, {
            'correo_destinatario': 'personal.maria@gmail.com',
            'observacion_notificacion': 'Se entregaron credenciales por memorándum interno',
            'enviar_email': '0'
        })
        self.assertEqual(resp_notif.status_code, 302)

        detalle.refresh_from_db()
        self.assertTrue(detalle.notificado)
        self.assertEqual(detalle.notificado_por, self.user_tic)
        self.assertIsNotNone(detalle.fecha_notificacion)

    def test_cancelar_solicitud(self):
        solicitud = SolicitudCorreo.objects.create(
            establecimiento=self.establecimiento,
            departamento_solicitante=self.depto_clinico,
            usuario_solicitante=self.user_normal,
            estado="PENDIENTE_RRHH"
        )

        self.client.login(username="usuario_normal", password="password123")
        url_cancelar = reverse("solicitud_correo:cancelar", args=[solicitud.pk])
        response = self.client.post(url_cancelar)
        self.assertEqual(response.status_code, 302)

        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, "CANCELADA")

    def test_historial_solicitud_view(self):
        # Crear solicitud y detalles con diferentes transiciones
        solicitud = SolicitudCorreo.objects.create(
            establecimiento=self.establecimiento,
            departamento_solicitante=self.depto_clinico,
            usuario_solicitante=self.user_normal,
            estado="PENDIENTE_RRHH"
        )
        detalle = SolicitudCorreoDetalle.objects.create(
            solicitud=solicitud,
            rut="12.345.678-9",
            nombres="Andrea",
            apellidos="Castillo",
            departamento="Medicina",
            estado="PENDIENTE_RRHH"
        )

        detalle.estado = "APROBADO_RRHH"
        detalle.usuario_rrhh = self.user_rrhh
        detalle.save()

        detalle.estado = "CREADO"
        detalle.correo_creado = "andrea.castillo@redsalud.gob.cl"
        detalle.tecnico_responsable = self.user_tic
        detalle.save()

        detalle.notificado = True
        detalle.notificado_por = self.user_tic
        detalle.save()

        self.client.login(username="usuario_normal", password="password123")
        url_historial = reverse("solicitud_correo:historial", args=[solicitud.pk])
        response = self.client.get(url_historial)
        self.assertEqual(response.status_code, 200)
        self.assertIn('eventos', response.context)
        self.assertGreater(len(response.context['eventos']), 0)

    def test_api_funcionario_info(self):
        self.client.login(username="usuario_normal", password="password123")
        url_api = reverse("solicitud_correo:api_funcionario_info", args=[self.funcionario_ejemplo.pk])
        response = self.client.get(url_api)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["rut"], self.funcionario_ejemplo.rut)
        self.assertEqual(data["nombres"], self.funcionario_ejemplo.nombres)
        self.assertEqual(data["apellidos"], self.funcionario_ejemplo.apellidos)
