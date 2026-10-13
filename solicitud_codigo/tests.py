from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from core.models.establecimientos import Establecimiento
from core.models.usuarios import User
from solicitud_codigo.forms import (
    SolicitudCodigoForm,
    ObservarSolicitudForm,
    RechazarSolicitudForm,
    CrearCodigoEfectivoForm,
)
from solicitud_codigo.models import (
    AreaSolicitud,
    SubareaSolicitud,
    MaestraCodigoSISSA,
    PerfilCodigo,
    SolicitudCodigo,
)
from solicitud_codigo.permissions import (
    user_can_solicitar,
    user_is_referente,
    user_can_validate,
    user_can_create_codes,
    user_can_manage_solicitud,
)


class SolicitudCodigoModelAndPermissionTests(TestCase):
    def setUp(self):
        self.establecimiento1 = Establecimiento.objects.create(
            nombre="Hospital San Pablo de Coquimbo",
            alias="HSP",
            region="Coquimbo"
        )
        self.establecimiento2 = Establecimiento.objects.create(
            nombre="Hospital de La Serena",
            alias="HLS",
            region="Coquimbo"
        )

        self.area_farmacia = AreaSolicitud.objects.create(
            nombre="Farmacia y Medicamentos",
            codigo="FARM"
        )
        self.subarea_farmacia = SubareaSolicitud.objects.create(
            area=self.area_farmacia,
            nombre="Antibióticos y Antimicrobianos",
            codigo="ANTIB"
        )

        self.area_insumos = AreaSolicitud.objects.create(
            nombre="Insumos Médicos y Quirúrgicos",
            codigo="INS"
        )

        self.user_solicitante = User.objects.create_user(
            username="solicitante1",
            password="Password123!",
            first_name="Carlos",
            last_name="Perez",
            establecimiento=self.establecimiento1
        )

        self.user_referente_area = User.objects.create_user(
            username="referente_farmacia",
            password="Password123!",
            first_name="Dra. Andrea",
            last_name="Gomez",
            establecimiento=self.establecimiento1
        )
        self.perfil_ref_area = PerfilCodigo.objects.create(
            usuario=self.user_referente_area,
            es_referente=True,
            es_referente_global=False,
            puede_validar=True,
            puede_crear_codigos=False
        )
        self.perfil_ref_area.areas_asignadas.add(self.area_farmacia)

        self.user_referente_global = User.objects.create_user(
            username="referente_global",
            password="Password123!",
            first_name="Juan",
            last_name="Valdivia",
            establecimiento=self.establecimiento1
        )
        self.perfil_ref_global = PerfilCodigo.objects.create(
            usuario=self.user_referente_global,
            es_referente=True,
            es_referente_global=True,
            puede_validar=True,
            puede_crear_codigos=False
        )

        self.user_creador_tic = User.objects.create_user(
            username="creador_tic",
            password="Password123!",
            first_name="Manuel",
            last_name="Rojas",
            establecimiento=self.establecimiento1
        )
        self.perfil_creador = PerfilCodigo.objects.create(
            usuario=self.user_creador_tic,
            es_referente=False,
            puede_validar=False,
            puede_crear_codigos=True
        )

    def test_model_str_representations(self):
        self.assertEqual(str(self.area_farmacia), "FARMACIA Y MEDICAMENTOS")
        self.assertEqual(
            str(self.subarea_farmacia),
            "FARMACIA Y MEDICAMENTOS - ANTIBIÓTICOS Y ANTIMICROBIANOS"
        )

        maestra = MaestraCodigoSISSA.objects.create(
            codigo="SIS-1001",
            nombre_producto="Paracetamol 500mg",
            presentacion="Caja x 100",
            area=self.area_farmacia
        )
        self.assertIn("SIS-1001", str(maestra))

    def test_perfil_codigo_permissions_helpers(self):
        self.assertTrue(user_can_solicitar(self.user_solicitante))
        self.assertTrue(user_is_referente(self.user_referente_area))
        self.assertTrue(user_is_referente(self.user_referente_global))
        self.assertFalse(user_is_referente(self.user_creador_tic))

        self.assertTrue(user_can_validate(self.user_referente_area))
        self.assertTrue(user_can_validate(self.user_referente_global))
        self.assertFalse(user_can_validate(self.user_creador_tic))

        self.assertTrue(user_can_create_codes(self.user_creador_tic))
        self.assertFalse(user_can_create_codes(self.user_referente_area))

    def test_generacion_folio_automatico_y_formato(self):
        solicitud = SolicitudCodigo.objects.create(
            usuario_solicitante=self.user_solicitante,
            establecimiento=self.establecimiento1,
            area=self.area_farmacia,
            subarea=self.subarea_farmacia,
            producto_base="Ciprofloxacino 500mg",
            presentacion="Caja x 20 comprimidos",
            descripcion_requerimiento="Insumo necesario para tratamiento ambulatorio",
            estado=SolicitudCodigo.ESTADO_PENDIENTE_VALIDACION
        )
        solicitud.numero_solicitud = solicitud.generar_folio()
        solicitud.save()

        year = timezone.now().year
        self.assertTrue(solicitud.numero_solicitud.startswith(f"COD-{year}-HSP-"))
        self.assertEqual(solicitud.numero_solicitud, f"COD-{year}-HSP-00001")

        # Segunda solicitud para el mismo establecimiento
        solicitud2 = SolicitudCodigo.objects.create(
            usuario_solicitante=self.user_solicitante,
            establecimiento=self.establecimiento1,
            area=self.area_farmacia,
            producto_base="Ibuprofeno 400mg",
            presentacion="Frasco jarabe 120ml",
            descripcion_requerimiento="Para pediatría",
            estado=SolicitudCodigo.ESTADO_PENDIENTE_VALIDACION
        )
        solicitud2.numero_solicitud = solicitud2.generar_folio()
        solicitud2.save()

        self.assertEqual(solicitud2.numero_solicitud, f"COD-{year}-HSP-00002")

    def test_ambito_referente_area_vs_global(self):
        sol_farmacia = SolicitudCodigo.objects.create(
            usuario_solicitante=self.user_solicitante,
            establecimiento=self.establecimiento1,
            area=self.area_farmacia,
            producto_base="Amoxicilina 500mg",
            presentacion="Caja x 100",
            descripcion_requerimiento="Stock clínico",
            numero_solicitud="COD-2026-HSP-00010"
        )
        sol_insumos = SolicitudCodigo.objects.create(
            usuario_solicitante=self.user_solicitante,
            establecimiento=self.establecimiento1,
            area=self.area_insumos,
            producto_base="Guantes de Procedimiento L",
            presentacion="Caja x 100",
            descripcion_requerimiento="Uso diario",
            numero_solicitud="COD-2026-HSP-00011"
        )

        # Referente de Farmacia puede gestionar sol_farmacia pero NO sol_insumos
        self.assertTrue(user_can_manage_solicitud(self.user_referente_area, sol_farmacia))
        self.assertFalse(user_can_manage_solicitud(self.user_referente_area, sol_insumos))

        # Referente Global puede gestionar AMBAS
        self.assertTrue(user_can_manage_solicitud(self.user_referente_global, sol_farmacia))
        self.assertTrue(user_can_manage_solicitud(self.user_referente_global, sol_insumos))

    def test_historial_eventos_y_trazabilidad(self):
        solicitud = SolicitudCodigo.objects.create(
            usuario_solicitante=self.user_solicitante,
            establecimiento=self.establecimiento1,
            area=self.area_farmacia,
            producto_base="Enalapril 10mg",
            presentacion="Caja x 30",
            descripcion_requerimiento="Programa cardiovascular",
            numero_solicitud="COD-2026-HSP-00020"
        )

        evento = solicitud.registrar_evento(
            usuario=self.user_solicitante,
            accion="Creación de Solicitud",
            estado_anterior=None,
            estado_nuevo="PENDIENTE_VALIDACION",
            detalle="Registro inicial"
        )

        self.assertEqual(solicitud.historial_eventos.count(), 1)
        self.assertEqual(evento.accion, "Creación de Solicitud")
        self.assertEqual(evento.usuario, self.user_solicitante)


class SolicitudCodigoFormsTests(TestCase):
    def setUp(self):
        self.area = AreaSolicitud.objects.create(nombre="Laboratorio Clínico", codigo="LAB")
        self.subarea = SubareaSolicitud.objects.create(area=self.area, nombre="Reactivos Bioquímicos")

    def test_solicitud_codigo_form_valido(self):
        form_data = {
            "area": self.area.id,
            "subarea": self.subarea.id,
            "producto_base": "Reactivo Glucosa Hexoquinasa",
            "presentacion": "Kit 4x50ml",
            "descripcion_requerimiento": "Para equipo automatizado de bioquímica",
            "antecedentes_complementarios": "Acreditación de laboratorio",
        }
        form = SolicitudCodigoForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_solicitud_codigo_form_campos_obligatorios(self):
        form = SolicitudCodigoForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("area", form.errors)
        self.assertIn("producto_base", form.errors)
        self.assertIn("presentacion", form.errors)
        self.assertIn("descripcion_requerimiento", form.errors)

    def test_observar_solicitud_form_requiere_justificacion_minima(self):
        form_invalido = ObservarSolicitudForm(data={"observaciones": "abc"})
        self.assertFalse(form_invalido.is_valid())
        self.assertIn("observaciones", form_invalido.errors)

        form_valido = ObservarSolicitudForm(data={"observaciones": "Favor detallar la concentración requerida."})
        self.assertTrue(form_valido.is_valid())

    def test_rechazar_solicitud_form_valido(self):
        form = RechazarSolicitudForm(data={"motivo_rechazo": "Producto descontinuado por el ISP."})
        self.assertTrue(form.is_valid())

    def test_crear_codigo_efectivo_form(self):
        form = CrearCodigoEfectivoForm(data={
            "codigo_creado": "COD-SISSA-2026-999",
            "observaciones_creacion": "Creado en el sistema central",
            "registrar_en_maestra": True
        })
        self.assertTrue(form.is_valid())


class SolicitudCodigoViewsAndFlowTests(TestCase):
    def setUp(self):
        self.establecimiento = Establecimiento.objects.create(
            nombre="Hospital San Pablo de Coquimbo",
            alias="HSP"
        )
        self.area = AreaSolicitud.objects.create(nombre="Farmacia", codigo="FARM")
        self.subarea = SubareaSolicitud.objects.create(area=self.area, nombre="Analgesia")

        self.solicitante = User.objects.create_user(
            username="solicitante_user",
            password="password123",
            first_name="Juan",
            last_name="Perez",
            establecimiento=self.establecimiento
        )

        self.otro_solicitante = User.objects.create_user(
            username="otro_user",
            password="password123",
            first_name="Maria",
            last_name="Lopez",
            establecimiento=self.establecimiento
        )

        self.referente = User.objects.create_user(
            username="referente_user",
            password="password123",
            first_name="Doctor",
            last_name="Referente",
            establecimiento=self.establecimiento
        )
        PerfilCodigo.objects.create(
            usuario=self.referente,
            es_referente=True,
            es_referente_global=True,
            puede_validar=True,
            puede_crear_codigos=False
        )

        self.creador_codigo = User.objects.create_user(
            username="creador_user",
            password="password123",
            first_name="Encargado",
            last_name="TIC",
            establecimiento=self.establecimiento
        )
        PerfilCodigo.objects.create(
            usuario=self.creador_codigo,
            es_referente=False,
            puede_crear_codigos=True
        )

        self.client = Client()

    def test_creacion_solicitud_flujo_completo(self):
        self.client.force_login(self.solicitante)

        url_crear = reverse("solicitud_codigo:crear")
        response = self.client.get(url_crear)
        self.assertEqual(response.status_code, 200)

        post_data = {
            "area": self.area.id,
            "subarea": self.subarea.id,
            "producto_base": "Ketorolaco Trometamol 30mg/ml",
            "presentacion": "Ampolla 1ml",
            "descripcion_requerimiento": "Uso endovenoso en urgencias",
            "antecedentes_complementarios": "Guía clínica de dolor agudo",
        }

        response = self.client.post(url_crear, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        solicitud = SolicitudCodigo.objects.filter(usuario_solicitante=self.solicitante).first()
        self.assertIsNotNone(solicitud)
        self.assertEqual(solicitud.estado, SolicitudCodigo.ESTADO_PENDIENTE_VALIDACION)
        self.assertEqual(solicitud.establecimiento, self.establecimiento)
        self.assertTrue(solicitud.numero_solicitud.startswith("COD-"))
        self.assertEqual(solicitud.historial_eventos.count(), 1)

    def test_mis_solicitudes_list_view_and_datatables_ajax(self):
        self.client.force_login(self.solicitante)

        sol1 = SolicitudCodigo.objects.create(
            usuario_solicitante=self.solicitante,
            establecimiento=self.establecimiento,
            area=self.area,
            producto_base="Paracetamol 500mg",
            presentacion="Caja x 100",
            descripcion_requerimiento="Stock regular",
            numero_solicitud="COD-2026-HSP-00101"
        )
        # Solicitud de otro usuario
        sol2 = SolicitudCodigo.objects.create(
            usuario_solicitante=self.otro_solicitante,
            establecimiento=self.establecimiento,
            area=self.area,
            producto_base="Morfina 10mg",
            presentacion="Ampolla",
            descripcion_requerimiento="Stock restringido",
            numero_solicitud="COD-2026-HSP-00102"
        )

        url = reverse("solicitud_codigo:mis_solicitudes")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Llamada AJAX de DataTables
        response_ajax = self.client.get(
            url,
            {"draw": "1", "start": "0", "length": "10"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response_ajax.status_code, 200)
        data = response_ajax.json()
        self.assertEqual(data["recordsTotal"], 1)
        self.assertEqual(len(data["data"]), 1)
        self.assertIn("COD-2026-HSP-00101", data["data"][0]["numero_solicitud"])

    def test_bandeja_referente_list_view_and_permissions(self):
        # Usuario normal no tiene acceso a bandeja del referente
        self.client.force_login(self.solicitante)
        url_ref = reverse("solicitud_codigo:bandeja_referente")
        response = self.client.get(url_ref)
        self.assertEqual(response.status_code, 403)

        # Referente autorizado sí tiene acceso
        self.client.force_login(self.referente)
        response_ref = self.client.get(url_ref)
        self.assertEqual(response_ref.status_code, 200)

        # Solicitud en base de datos
        SolicitudCodigo.objects.create(
            usuario_solicitante=self.solicitante,
            establecimiento=self.establecimiento,
            area=self.area,
            producto_base="Ibuprofeno 600mg",
            presentacion="Caja x 20",
            descripcion_requerimiento="Dolor articular",
            numero_solicitud="COD-2026-HSP-00201"
        )

        response_ajax = self.client.get(
            url_ref,
            {"draw": "1", "start": "0", "length": "10"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response_ajax.status_code, 200)
        data = response_ajax.json()
        self.assertEqual(data["recordsTotal"], 1)

    def test_seguridad_acceso_detalle_no_autorizado(self):
        solicitud = SolicitudCodigo.objects.create(
            usuario_solicitante=self.solicitante,
            establecimiento=self.establecimiento,
            area=self.area,
            producto_base="Insumo Privado",
            presentacion="Unidad",
            descripcion_requerimiento="Test",
            numero_solicitud="COD-2026-HSP-00301"
        )

        # Otro solicitante intenta ver el detalle por URL directa -> 403
        self.client.force_login(self.otro_solicitante)
        response = self.client.get(reverse("solicitud_codigo:detalle", kwargs={"pk": solicitud.pk}))
        self.assertEqual(response.status_code, 403)

        # El dueño sí puede verlo -> 200
        self.client.force_login(self.solicitante)
        response_ok = self.client.get(reverse("solicitud_codigo:detalle", kwargs={"pk": solicitud.pk}))
        self.assertEqual(response_ok.status_code, 200)

    def test_flujo_observacion_y_correccion_solicitud(self):
        solicitud = SolicitudCodigo.objects.create(
            usuario_solicitante=self.solicitante,
            establecimiento=self.establecimiento,
            area=self.area,
            producto_base="Ketoprofeno",
            presentacion="Frasco",
            descripcion_requerimiento="Dolor",
            numero_solicitud="COD-2026-HSP-00401",
            estado=SolicitudCodigo.ESTADO_PENDIENTE_VALIDACION
        )

        # 1. Referente observa la solicitud
        self.client.force_login(self.referente)
        url_observar = reverse("solicitud_codigo:observar", kwargs={"pk": solicitud.pk})
        response_obs = self.client.post(
            url_observar,
            {"observaciones": "Especifique si es comprimido o inyectable y la dosis exacta."},
            follow=True
        )
        self.assertEqual(response_obs.status_code, 200)

        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, SolicitudCodigo.ESTADO_OBSERVADA)
        self.assertEqual(solicitud.usuario_referente, self.referente)
        self.assertIsNotNone(solicitud.fecha_observacion)

        # 2. Solicitante corrige y reenvía
        self.client.force_login(self.solicitante)
        url_corregir = reverse("solicitud_codigo:corregir", kwargs={"pk": solicitud.pk})

        response_corregir_get = self.client.get(url_corregir)
        self.assertEqual(response_corregir_get.status_code, 200)

        post_corregido = {
            "area": self.area.id,
            "subarea": self.subarea.id,
            "producto_base": "Ketoprofeno 100mg Comprimidos Recubiertos",
            "presentacion": "Caja x 30 comprimidos",
            "descripcion_requerimiento": "Uso para analgesia postquirúrgica",
            "antecedentes_complementarios": "Aprobado por comité de farmacia",
        }
        response_corregir_post = self.client.post(url_corregir, data=post_corregido, follow=True)
        self.assertEqual(response_corregir_post.status_code, 200)

        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, SolicitudCodigo.ESTADO_PENDIENTE_VALIDACION)
        self.assertEqual(solicitud.producto_base, "KETOPROFENO 100MG COMPRIMIDOS RECUBIERTOS")
        self.assertIsNotNone(solicitud.fecha_reenvio)

    def test_flujo_rechazo_solicitud(self):
        solicitud = SolicitudCodigo.objects.create(
            usuario_solicitante=self.solicitante,
            establecimiento=self.establecimiento,
            area=self.area,
            producto_base="Medicamento Prohibido",
            presentacion="Frasco",
            descripcion_requerimiento="Test",
            numero_solicitud="COD-2026-HSP-00501",
            estado=SolicitudCodigo.ESTADO_PENDIENTE_VALIDACION
        )

        self.client.force_login(self.referente)
        url_rechazar = reverse("solicitud_codigo:rechazar", kwargs={"pk": solicitud.pk})
        response = self.client.post(
            url_rechazar,
            {"motivo_rechazo": "Fármaco retirado del mercado por alerta sanitaria del ISP."},
            follow=True
        )
        self.assertEqual(response.status_code, 200)

        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, SolicitudCodigo.ESTADO_RECHAZADA)
        self.assertIsNotNone(solicitud.fecha_rechazo)

        # No se debe poder corregir una solicitud rechazada
        self.client.force_login(self.solicitante)
        url_corregir = reverse("solicitud_codigo:corregir", kwargs={"pk": solicitud.pk})
        response_corregir = self.client.get(url_corregir, follow=True)
        # Redirige con error
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, SolicitudCodigo.ESTADO_RECHAZADA)

    def test_flujo_validacion_y_creacion_efectiva_codigo(self):
        solicitud = SolicitudCodigo.objects.create(
            usuario_solicitante=self.solicitante,
            establecimiento=self.establecimiento,
            area=self.area,
            subarea=self.subarea,
            producto_base="Salbutamol Aerosol 100mcg",
            presentacion="Inhalador 200 dosis",
            descripcion_requerimiento="Programa respiratorio ERA",
            numero_solicitud="COD-2026-HSP-00601",
            estado=SolicitudCodigo.ESTADO_PENDIENTE_VALIDACION
        )

        # 1. Referente Valida
        self.client.force_login(self.referente)
        url_validar = reverse("solicitud_codigo:validar", kwargs={"pk": solicitud.pk})
        response_val = self.client.post(
            url_validar,
            {"observaciones": "Cumple con el petitorio respiratorio ministerial."},
            follow=True
        )
        self.assertEqual(response_val.status_code, 200)

        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, SolicitudCodigo.ESTADO_VALIDADA)
        self.assertIsNotNone(solicitud.fecha_validacion)

        # 2. Creador TIC revisa bandeja de pendientes de creación
        self.client.force_login(self.creador_codigo)
        url_bandeja_creacion = reverse("solicitud_codigo:bandeja_creacion")
        response_creacion = self.client.get(url_bandeja_creacion)
        self.assertEqual(response_creacion.status_code, 200)

        # 3. Creador registra el código final
        url_crear_cod = reverse("solicitud_codigo:crear_codigo", kwargs={"pk": solicitud.pk})
        response_final = self.client.post(
            url_crear_cod,
            {
                "codigo_creado": "SISSA-MED-2026-888",
                "observaciones_creacion": "Creado en el catálogo maestro SISSA con codificación oficial.",
                "registrar_en_maestra": True
            },
            follow=True
        )
        self.assertEqual(response_final.status_code, 200)

        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, SolicitudCodigo.ESTADO_CODIGO_CREADO)
        self.assertEqual(solicitud.codigo_creado, "SISSA-MED-2026-888")
        self.assertEqual(solicitud.usuario_creador_codigo, self.creador_codigo)
        self.assertIsNotNone(solicitud.fecha_creacion_codigo)

        # Verificar que se registró en MaestraCodigoSISSA
        maestra_item = MaestraCodigoSISSA.objects.filter(codigo="SISSA-MED-2026-888").first()
        self.assertIsNotNone(maestra_item)
        self.assertIn("SALBUTAMOL", maestra_item.nombre_producto.upper())

    def test_ajax_endpoints_subareas_y_coincidencias(self):
        self.client.force_login(self.solicitante)

        # 1. API Subareas
        url_subareas = reverse("solicitud_codigo:api_subareas")
        res_sub = self.client.get(url_subareas, {"area_id": self.area.id})
        self.assertEqual(res_sub.status_code, 200)
        data_sub = res_sub.json()
        self.assertEqual(len(data_sub["subareas"]), 1)
        self.assertEqual(data_sub["subareas"][0]["nombre"], "ANALGESIA")

        # 2. API Coincidencias en Maestra
        MaestraCodigoSISSA.objects.create(
            codigo="COD-SISSA-777",
            nombre_producto="Omeprazol 20mg",
            presentacion="Frasco x 30 cápsulas",
            area=self.area
        )

        url_coincidencias = reverse("solicitud_codigo:api_coincidencias")
        res_coin = self.client.get(url_coincidencias, {"q": "Omeprazol", "area_id": self.area.id})
        self.assertEqual(res_coin.status_code, 200)
        data_coin = res_coin.json()
        self.assertGreaterEqual(data_coin["total"], 1)
        self.assertEqual(data_coin["coincidencias"][0]["codigo"], "COD-SISSA-777")
