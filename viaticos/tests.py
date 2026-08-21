from django.test import TestCase, Client
from django.urls import reverse

from core.models.establecimientos import Establecimiento
from core.models.funcionario import Funcionario
from core.models.unidad_organizacional import UnidadOrganizacional
from core.models.usuarios import User
from viaticos.models import (
    LugarDestino,
    EscalaViatico,
    VistoLegal,
    SolicitudCometidoViatico,
)


class ViaticosModuleTests(TestCase):
    def setUp(self):
        self.establecimiento = Establecimiento.objects.create(
            nombre="Dirección Regional Coquimbo",
            alias="DR Coquimbo",
            region="Coquimbo"
        )

        self.unidad = UnidadOrganizacional.objects.create(
            nombre="Departamento de Protección Agrícola",
            es_departamento=True,
            establecimiento=self.establecimiento
        )

        self.funcionario = Funcionario.objects.create(
            rut="12345678-9",
            nombres="Juan Carlos",
            apellidos="Pérez Gómez",
            nombre="Juan Carlos Pérez Gómez",
            establecimiento=self.establecimiento,
            unidad_organizacional=self.unidad,
            cargo="Inspector Fitosanitario"
        )

        self.user = User.objects.create_user(
            username="jperez",
            password="password123",
            first_name="Juan",
            last_name="Perez",
            establecimiento=self.establecimiento,
            funcionario=self.funcionario,
            is_staff=True,
            is_superuser=True
        )

        self.client = Client()
        self.client.login(username="JPEREZ", password="password123")

        # Catálogos iniciales
        self.lugar = LugarDestino.objects.create(
            codigo="LUG-01",
            nombre="Vicuña",
            region="Coquimbo",
            comuna="Vicuña",
            establecimiento=self.establecimiento
        )

        self.escala = EscalaViatico.objects.create(
            ano_vigencia=2026,
            grado_desde="1",
            grado_hasta="20",
            valor_100_pernocta=65000,
            valor_50_parcial=32500,
            valor_faena=15000
        )

        self.visto = VistoLegal.objects.create(
            codigo="V-01",
            texto_visto="La Ley N° 18.755 Orgánica del SAG...",
            establecimiento=self.establecimiento
        )

    def test_dashboard_view(self):
        url = reverse('viaticos:dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'viaticos/dashboard.html')

    def test_solicitud_lifecycle(self):
        # 1. Crear Solicitud
        create_url = reverse('viaticos:solicitud_create')
        post_data = {
            'action': 'add',
            'tipo_solicitud': 'COMETIDO_VIATICO',
            'funcionario': self.funcionario.pk,
            'unidad_organizacional': self.unidad.pk,
            'cargo_desempenado': 'Inspector Fitosanitario',
            'grado_funcionario': '10',
            'motivo_viaje': 'Fiscalización fitosanitaria predial en Valle de Elqui',
            'fecha_inicio': '2026-09-01',
            'fecha_termino': '2026-09-03',
            'hora_salida': '08:00',
            'hora_llegada': '18:00',
            'total_dias': 3,
            'tiene_derecho_pasaje': True,
            'requiere_vehiculo_institucional': True,
        }
        response = self.client.post(create_url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        solicitud = SolicitudCometidoViatico.objects.first()
        self.assertIsNotNone(solicitud)
        self.assertEqual(solicitud.estado, 'BORRADOR')
        self.assertEqual(solicitud.folio, 1)

        # 2. Agregar Tramo / Itinerario
        itinerario_url = reverse('viaticos:itinerario_create', kwargs={'solicitud_id': solicitud.id})
        itinerario_data = {
            'action': 'add',
            'orden_visita': 1,
            'lugar_destino': self.lugar.pk,
            'descripcion_actividad_lugar': 'Inspección de cuarteles de vid',
            'fecha_llegada': '2026-09-01',
            'fecha_salida': '2026-09-03',
            'medio_transporte_tramo': 'VEHICULO_INSTITUCIONAL',
            'pernocta_en_lugar': True,
        }
        res_itin = self.client.post(itinerario_url, data=itinerario_data, follow=True)
        self.assertEqual(res_itin.status_code, 200)
        self.assertEqual(solicitud.itinerarios.count(), 1)

        # 3. Enviar a Jefatura
        enviar_url = reverse('viaticos:solicitud_enviar_jefatura', kwargs={'pk': solicitud.id})
        self.client.get(enviar_url, follow=True)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, 'ENVIADO_JEFATURA')

        # 4. Aprobación Jefatura
        aprobar_url = reverse('viaticos:aprobacion_create', kwargs={'solicitud_id': solicitud.id})
        aprobacion_data = {
            'action': 'add',
            'etapa': 'JEFE_DIRECTO',
            'accion': 'APROBADO',
            'en_calidad_de': 'Jefe de Departamento',
            'firmado_con_fea': True,
            'observaciones': 'Cometido autorizado y necesario.',
        }
        self.client.post(aprobar_url, data=aprobacion_data, follow=True)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, 'EN_REVISION_SSGG')

        # 5. Aprobación SSGG
        aprobacion_ssgg_data = {
            'action': 'add',
            'etapa': 'SERVICIOS_GENERALES',
            'accion': 'APROBADO',
            'en_calidad_de': 'Encargado de Transporte',
            'firmado_con_fea': True,
            'observaciones': 'Vehículo institucional asignado.',
        }
        self.client.post(aprobar_url, data=aprobacion_ssgg_data, follow=True)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, 'EN_REVISION_RRHH')

        # 6. Aprobación RRHH
        aprobacion_rrhh_data = {
            'action': 'add',
            'etapa': 'RRHH_CONTROL',
            'accion': 'APROBADO',
            'en_calidad_de': 'Jefe de Personal',
            'firmado_con_fea': True,
            'observaciones': 'Cumple normativa de viáticos.',
        }
        self.client.post(aprobar_url, data=aprobacion_rrhh_data, follow=True)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, 'RESOLUCION_EMITIDA')

    def test_catalogos_views(self):
        # Lugar
        res = self.client.get(reverse('viaticos:lugar_list'))
        self.assertEqual(res.status_code, 200)

        # Escala
        res = self.client.get(reverse('viaticos:escala_list'))
        self.assertEqual(res.status_code, 200)

        # Visto Legal
        res = self.client.get(reverse('viaticos:visto_list'))
        self.assertEqual(res.status_code, 200)

    def test_transporte_views(self):
        res = self.client.get(reverse('viaticos:transporte_list'))
        self.assertEqual(res.status_code, 200)

    def test_resoluciones_views(self):
        res = self.client.get(reverse('viaticos:resolucion_list'))
        self.assertEqual(res.status_code, 200)

    def test_finanzas_views(self):
        res = self.client.get(reverse('viaticos:egreso_list'))
        self.assertEqual(res.status_code, 200)
        res_rend = self.client.get(reverse('viaticos:rendicion_list'))
        self.assertEqual(res_rend.status_code, 200)

    def test_asistencia_views(self):
        res = self.client.get(reverse('viaticos:reloj_list'))
        self.assertEqual(res.status_code, 200)
        res_gremial = self.client.get(reverse('viaticos:permiso_gremial_list'))
        self.assertEqual(res_gremial.status_code, 200)

    def test_mis_solicitudes_view(self):
        res = self.client.get(reverse('viaticos:mis_solicitudes_list'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['list_url_name'], 'viaticos:mis_solicitudes_list')
        self.assertEqual(res.context['create_url_name'], 'viaticos:solicitud_create')
        self.assertEqual(res.context['update_url_name'], 'viaticos:solicitud_update')
        self.assertEqual(res.context['delete_url_name'], 'viaticos:solicitud_delete')
        self.assertEqual(res.context['list_url'], reverse('viaticos:mis_solicitudes_list'))
        self.assertEqual(res.context['create_url'], reverse('viaticos:solicitud_create'))

    def test_solicitud_list_view(self):
        res = self.client.get(reverse('viaticos:solicitud_list'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['list_url_name'], 'viaticos:solicitud_list')
        self.assertEqual(res.context['create_url_name'], 'viaticos:solicitud_create')
