from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from bodega.models.producto import Producto
from core.models.establecimientos import Establecimiento
from solicitud_codigo.forms import (
    SolicitudCodigoForm,
    SolicitudCodigoCorregirForm,
    ObservarSolicitudForm,
    RechazarSolicitudForm,
    ValidarSolicitudForm,
    CrearCodigoEfectivoForm,
)
from solicitud_codigo.models import (
    AreaSolicitud,
    SubareaSolicitud,
    MaestraCodigoSISSA,
    SolicitudCodigo,
)
from solicitud_codigo.permissions import (
    SolicitanteRequiredMixin,
    ReferenteRequiredMixin,
    CreadorCodigoRequiredMixin,
    get_perfil_codigo,
    user_can_create_codes,
    user_can_manage_solicitud,
)


def get_estado_badge(estado):
    badges = {
        SolicitudCodigo.ESTADO_PENDIENTE_VALIDACION: '<span class="badge bg-warning text-dark"><i class="bi bi-hourglass-split me-1"></i>Pendiente de Validación</span>',
        SolicitudCodigo.ESTADO_OBSERVADA: '<span class="badge bg-info text-dark"><i class="bi bi-exclamation-circle me-1"></i>Observada</span>',
        SolicitudCodigo.ESTADO_VALIDADA: '<span class="badge bg-primary"><i class="bi bi-check2-circle me-1"></i>Validada</span>',
        SolicitudCodigo.ESTADO_PENDIENTE_CREACION: '<span class="badge bg-secondary"><i class="bi bi-gear-wide-connected me-1"></i>Pendiente de Creación</span>',
        SolicitudCodigo.ESTADO_RECHAZADA: '<span class="badge bg-danger"><i class="bi bi-x-circle me-1"></i>Rechazada</span>',
        SolicitudCodigo.ESTADO_CODIGO_CREADO: '<span class="badge bg-success"><i class="bi bi-check-all me-1"></i>Código Creado</span>',
    }
    return badges.get(estado, f'<span class="badge bg-secondary">{escape(estado)}</span>')


# ==============================================================================
# 1. BANDEJA DEL SOLICITANTE
# ==============================================================================
class MisSolicitudesListView(SolicitanteRequiredMixin, ListView):
    model = SolicitudCodigo
    template_name = "solicitud_codigo/mis_solicitudes.html"
    context_object_name = "solicitudes"

    view_title = "Mis Solicitudes de Códigos SISSA"
    view_type = "CBV"

    columns = [
        "numero_solicitud",
        "fecha_solicitud",
        "area__nombre",
        "subarea__nombre",
        "producto_base",
        "presentacion",
        "estado",
        "acciones",
    ]

    searchable_columns = [
        "numero_solicitud",
        "producto_base",
        "presentacion",
        "descripcion_requerimiento",
        "area__nombre",
        "subarea__nombre",
    ]

    def get_queryset(self):
        return (
            SolicitudCodigo.objects
            .filter(usuario_solicitante=self.request.user, is_active=True)
            .select_related("area", "subarea", "establecimiento", "usuario_referente")
            .order_by("-fecha_solicitud", "-id")
        )

    def get_column_control_options(self):
        areas = (
            AreaSolicitud.objects
            .filter(is_active=True)
            .values_list("nombre", flat=True)
            .distinct()
            .order_by("nombre")
        )

        estados = [
            {"label": label, "value": code}
            for code, label in SolicitudCodigo.ESTADOS
        ]

        return {
            "area__nombre": [
                {"label": nombre, "value": nombre}
                for nombre in areas
                if nombre
            ],
            "estado": estados,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_title"] = self.view_title
        context["view_type"] = self.view_type
        context["column_control_options"] = self.get_column_control_options()
        return context

    def get(self, request, *args, **kwargs):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return self.datatables_response(request)
        return super().get(request, *args, **kwargs)

    def datatables_response(self, request):
        queryset = self.get_queryset()

        draw = int(request.GET.get("draw", 1))
        start = max(int(request.GET.get("start", 0)), 0)
        length = int(request.GET.get("length", 10))

        records_total = queryset.count()

        # Búsqueda global
        search_value = request.GET.get("search[value]", "").strip()
        if search_value:
            search_query = Q()
            for column in self.searchable_columns:
                search_query |= Q(**{f"{column}__icontains": search_value})
            queryset = queryset.filter(search_query)

        # Filtro de columna para Área (columna índice 2)
        area_filter = request.GET.get("columns[2][search][value]", "").strip()
        if area_filter:
            queryset = queryset.filter(area__nombre__icontains=area_filter)

        # Filtro de columna para Estado (columna índice 6)
        estado_filter = request.GET.get("columns[6][search][value]", "").strip()
        if estado_filter:
            queryset = queryset.filter(estado=estado_filter)

        records_filtered = queryset.count()

        # Ordenamiento
        order_column = request.GET.get("order[0][column]")
        order_dir = request.GET.get("order[0][dir]", "desc")

        order_map = {
            0: "numero_solicitud",
            1: "fecha_solicitud",
            2: "area__nombre",
            3: "subarea__nombre",
            4: "producto_base",
            5: "presentacion",
            6: "estado",
        }

        if order_column is not None:
            try:
                col_idx = int(order_column)
                field = order_map.get(col_idx)
                if field:
                    if order_dir == "desc":
                        field = f"-{field}"
                    queryset = queryset.order_by(field)
            except (ValueError, TypeError):
                pass

        if length != -1:
            queryset = queryset[start:start + min(length, 500)]

        data = [
            self.serialize_solicitud(solicitud)
            for solicitud in queryset
        ]

        return JsonResponse({
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data,
        })

    def serialize_solicitud(self, sol):
        detalle_url = reverse("solicitud_codigo:detalle", kwargs={"pk": sol.pk})
        corregir_url = reverse("solicitud_codigo:corregir", kwargs={"pk": sol.pk})

        botones_html = f'<div class="btn-group btn-group-sm" role="group">'
        botones_html += f'<a href="{detalle_url}" class="btn btn-outline-primary" title="Ver Detalle"><i class="bi bi-eye"></i></a>'

        if sol.estado == SolicitudCodigo.ESTADO_OBSERVADA:
            botones_html += f'<a href="{corregir_url}" class="btn btn-warning" title="Corregir Solicitud Observada"><i class="bi bi-pencil-square me-1"></i>Corregir</a>'

        botones_html += '</div>'

        return {
            "numero_solicitud": sol.numero_solicitud or f"SOL-{sol.pk}",
            "fecha_solicitud": sol.fecha_solicitud.strftime("%d/%m/%Y %H:%M") if sol.fecha_solicitud else "",
            "area__nombre": sol.area.nombre if sol.area else "",
            "subarea__nombre": sol.subarea.nombre if sol.subarea else "—",
            "producto_base": escape(sol.producto_base),
            "presentacion": escape(sol.presentacion),
            "estado": get_estado_badge(sol.estado),
            "acciones": botones_html,
        }


# ==============================================================================
# 2. BANDEJA DEL REFERENTE GLOBAL
# ==============================================================================
class BandejaReferenteListView(ReferenteRequiredMixin, ListView):
    model = SolicitudCodigo
    template_name = "solicitud_codigo/bandeja_referente.html"
    context_object_name = "solicitudes"

    view_title = "Bandeja de Validación — Referente Global de Códigos"
    view_type = "CBV"

    columns = [
        "numero_solicitud",
        "fecha_solicitud",
        "establecimiento__nombre",
        "usuario_solicitante__nombre",
        "area__nombre",
        "subarea__nombre",
        "producto_base",
        "estado",
        "acciones",
    ]

    searchable_columns = [
        "numero_solicitud",
        "producto_base",
        "presentacion",
        "descripcion_requerimiento",
        "establecimiento__nombre",
        "establecimiento__alias",
        "usuario_solicitante__first_name",
        "usuario_solicitante__last_name",
        "usuario_solicitante__username",
        "area__nombre",
        "subarea__nombre",
    ]

    def get_queryset(self):
        perfil = get_perfil_codigo(self.request.user)
        if not perfil or not perfil.es_referente:
            return SolicitudCodigo.objects.none()

        qs = (
            SolicitudCodigo.objects
            .filter(is_active=True)
            .select_related("area", "subarea", "establecimiento", "usuario_solicitante", "usuario_referente")
        )

        if not perfil.es_referente_global:
            areas_ids = perfil.areas_asignadas.values_list("id", flat=True)
            qs = qs.filter(area_id__in=areas_ids)

        return qs.order_by("-fecha_solicitud", "-id")

    def get_column_control_options(self):
        perfil = get_perfil_codigo(self.request.user)

        if perfil and perfil.es_referente_global:
            areas_qs = AreaSolicitud.objects.filter(is_active=True)
        elif perfil:
            areas_qs = perfil.areas_asignadas.filter(is_active=True)
        else:
            areas_qs = AreaSolicitud.objects.none()

        areas = areas_qs.values_list("nombre", flat=True).distinct().order_by("nombre")

        establecimientos = (
            Establecimiento.objects
            .filter(is_active=True)
            .values_list("nombre", flat=True)
            .distinct()
            .order_by("nombre")
        )

        estados = [
            {"label": label, "value": code}
            for code, label in SolicitudCodigo.ESTADOS
        ]

        return {
            "establecimiento__nombre": [
                {"label": nombre, "value": nombre}
                for nombre in establecimientos
                if nombre
            ],
            "area__nombre": [
                {"label": nombre, "value": nombre}
                for nombre in areas
                if nombre
            ],
            "estado": estados,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_title"] = self.view_title
        context["view_type"] = self.view_type
        context["column_control_options"] = self.get_column_control_options()
        return context

    def get(self, request, *args, **kwargs):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return self.datatables_response(request)
        return super().get(request, *args, **kwargs)

    def datatables_response(self, request):
        queryset = self.get_queryset()

        draw = int(request.GET.get("draw", 1))
        start = max(int(request.GET.get("start", 0)), 0)
        length = int(request.GET.get("length", 10))

        records_total = queryset.count()

        # Búsqueda global
        search_value = request.GET.get("search[value]", "").strip()
        if search_value:
            search_query = Q()
            for column in self.searchable_columns:
                search_query |= Q(**{f"{column}__icontains": search_value})
            queryset = queryset.filter(search_query)

        # Filtro de columna: Establecimiento (índice 2)
        est_filter = request.GET.get("columns[2][search][value]", "").strip()
        if est_filter:
            queryset = queryset.filter(establecimiento__nombre__icontains=est_filter)

        # Filtro de columna: Área (índice 4)
        area_filter = request.GET.get("columns[4][search][value]", "").strip()
        if area_filter:
            queryset = queryset.filter(area__nombre__icontains=area_filter)

        # Filtro de columna: Estado (índice 7)
        estado_filter = request.GET.get("columns[7][search][value]", "").strip()
        if estado_filter:
            queryset = queryset.filter(estado=estado_filter)

        records_filtered = queryset.count()

        # Ordenamiento
        order_column = request.GET.get("order[0][column]")
        order_dir = request.GET.get("order[0][dir]", "desc")

        order_map = {
            0: "numero_solicitud",
            1: "fecha_solicitud",
            2: "establecimiento__nombre",
            3: "usuario_solicitante__first_name",
            4: "area__nombre",
            5: "subarea__nombre",
            6: "producto_base",
            7: "estado",
        }

        if order_column is not None:
            try:
                col_idx = int(order_column)
                field = order_map.get(col_idx)
                if field:
                    if order_dir == "desc":
                        field = f"-{field}"
                    queryset = queryset.order_by(field)
            except (ValueError, TypeError):
                pass

        if length != -1:
            queryset = queryset[start:start + min(length, 500)]

        data = [
            self.serialize_solicitud(solicitud)
            for solicitud in queryset
        ]

        return JsonResponse({
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data,
        })

    def serialize_solicitud(self, sol):
        detalle_url = reverse("solicitud_codigo:detalle", kwargs={"pk": sol.pk})

        botones_html = f'<div class="btn-group btn-group-sm" role="group">'
        if sol.estado == SolicitudCodigo.ESTADO_PENDIENTE_VALIDACION:
            botones_html += f'<a href="{detalle_url}" class="btn btn-primary" title="Revisar y Validar Solicitud"><i class="bi bi-shield-check me-1"></i>Gestionar</a>'
        else:
            botones_html += f'<a href="{detalle_url}" class="btn btn-outline-secondary" title="Ver Detalle"><i class="bi bi-eye"></i></a>'
        botones_html += '</div>'

        solicitante_nom = sol.usuario_solicitante.get_full_name() or sol.usuario_solicitante.username if sol.usuario_solicitante else ""

        return {
            "numero_solicitud": sol.numero_solicitud or f"SOL-{sol.pk}",
            "fecha_solicitud": sol.fecha_solicitud.strftime("%d/%m/%Y %H:%M") if sol.fecha_solicitud else "",
            "establecimiento__nombre": sol.establecimiento.alias or sol.establecimiento.nombre if sol.establecimiento else "",
            "usuario_solicitante__nombre": escape(solicitante_nom),
            "area__nombre": sol.area.nombre if sol.area else "",
            "subarea__nombre": sol.subarea.nombre if sol.subarea else "—",
            "producto_base": escape(sol.producto_base),
            "estado": get_estado_badge(sol.estado),
            "acciones": botones_html,
        }


# ==============================================================================
# 3. BANDEJA DE SOLICITUDES VALIDADAS PENDIENTES DE CREACIÓN EFECTIVA
# ==============================================================================
class BandejaPendientesCreacionListView(CreadorCodigoRequiredMixin, ListView):
    model = SolicitudCodigo
    template_name = "solicitud_codigo/bandeja_creacion.html"
    context_object_name = "solicitudes"

    view_title = "Bandeja de Creación Efectiva de Códigos SISSA"
    view_type = "CBV"

    columns = [
        "numero_solicitud",
        "fecha_validacion",
        "establecimiento__nombre",
        "usuario_solicitante__nombre",
        "area__nombre",
        "producto_base",
        "presentacion",
        "usuario_referente__nombre",
        "estado",
        "acciones",
    ]

    searchable_columns = [
        "numero_solicitud",
        "producto_base",
        "presentacion",
        "descripcion_requerimiento",
        "establecimiento__nombre",
        "usuario_solicitante__first_name",
        "usuario_solicitante__last_name",
        "area__nombre",
    ]

    def get_queryset(self):
        return (
            SolicitudCodigo.objects
            .filter(
                estado__in=[
                    SolicitudCodigo.ESTADO_VALIDADA,
                    SolicitudCodigo.ESTADO_PENDIENTE_CREACION,
                ],
                is_active=True
            )
            .select_related("area", "subarea", "establecimiento", "usuario_solicitante", "usuario_referente")
            .order_by("fecha_validacion", "-id")
        )

    def get_column_control_options(self):
        areas = (
            AreaSolicitud.objects
            .filter(is_active=True)
            .values_list("nombre", flat=True)
            .distinct()
            .order_by("nombre")
        )

        establecimientos = (
            Establecimiento.objects
            .filter(is_active=True)
            .values_list("nombre", flat=True)
            .distinct()
            .order_by("nombre")
        )

        return {
            "establecimiento__nombre": [
                {"label": nombre, "value": nombre}
                for nombre in establecimientos
                if nombre
            ],
            "area__nombre": [
                {"label": nombre, "value": nombre}
                for nombre in areas
                if nombre
            ],
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_title"] = self.view_title
        context["view_type"] = self.view_type
        context["column_control_options"] = self.get_column_control_options()
        return context

    def get(self, request, *args, **kwargs):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return self.datatables_response(request)
        return super().get(request, *args, **kwargs)

    def datatables_response(self, request):
        queryset = self.get_queryset()

        draw = int(request.GET.get("draw", 1))
        start = max(int(request.GET.get("start", 0)), 0)
        length = int(request.GET.get("length", 10))

        records_total = queryset.count()

        search_value = request.GET.get("search[value]", "").strip()
        if search_value:
            search_query = Q()
            for column in self.searchable_columns:
                search_query |= Q(**{f"{column}__icontains": search_value})
            queryset = queryset.filter(search_query)

        # Filtro de columna: Establecimiento (índice 2)
        est_filter = request.GET.get("columns[2][search][value]", "").strip()
        if est_filter:
            queryset = queryset.filter(establecimiento__nombre__icontains=est_filter)

        # Filtro de columna: Área (índice 4)
        area_filter = request.GET.get("columns[4][search][value]", "").strip()
        if area_filter:
            queryset = queryset.filter(area__nombre__icontains=area_filter)

        records_filtered = queryset.count()

        # Ordenamiento
        order_column = request.GET.get("order[0][column]")
        order_dir = request.GET.get("order[0][dir]", "asc")

        order_map = {
            0: "numero_solicitud",
            1: "fecha_validacion",
            2: "establecimiento__nombre",
            3: "usuario_solicitante__first_name",
            4: "area__nombre",
            5: "producto_base",
            6: "presentacion",
            7: "usuario_referente__first_name",
            8: "estado",
        }

        if order_column is not None:
            try:
                col_idx = int(order_column)
                field = order_map.get(col_idx)
                if field:
                    if order_dir == "desc":
                        field = f"-{field}"
                    queryset = queryset.order_by(field)
            except (ValueError, TypeError):
                pass

        if length != -1:
            queryset = queryset[start:start + min(length, 500)]

        data = [
            self.serialize_solicitud(solicitud)
            for solicitud in queryset
        ]

        return JsonResponse({
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data,
        })

    def serialize_solicitud(self, sol):
        detalle_url = reverse("solicitud_codigo:detalle", kwargs={"pk": sol.pk})

        botones_html = f'<div class="btn-group btn-group-sm" role="group">'
        botones_html += f'<a href="{detalle_url}" class="btn btn-success" title="Registrar Código SISSA Creado"><i class="bi bi-plus-circle me-1"></i>Registrar Código</a>'
        botones_html += '</div>'

        solicitante_nom = sol.usuario_solicitante.get_full_name() or sol.usuario_solicitante.username if sol.usuario_solicitante else ""
        referente_nom = sol.usuario_referente.get_full_name() or sol.usuario_referente.username if sol.usuario_referente else "—"

        return {
            "numero_solicitud": sol.numero_solicitud or f"SOL-{sol.pk}",
            "fecha_validacion": sol.fecha_validacion.strftime("%d/%m/%Y %H:%M") if sol.fecha_validacion else "",
            "establecimiento__nombre": sol.establecimiento.alias or sol.establecimiento.nombre if sol.establecimiento else "",
            "usuario_solicitante__nombre": escape(solicitante_nom),
            "area__nombre": sol.area.nombre if sol.area else "",
            "producto_base": escape(sol.producto_base),
            "presentacion": escape(sol.presentacion),
            "usuario_referente__nombre": escape(referente_nom),
            "estado": get_estado_badge(sol.estado),
            "acciones": botones_html,
        }


# ==============================================================================
# 4. CREACIÓN DE NUEVA SOLICITUD
# ==============================================================================
class SolicitudCreateView(SolicitanteRequiredMixin, CreateView):
    model = SolicitudCodigo
    form_class = SolicitudCodigoForm
    template_name = "solicitud_codigo/solicitud_form.html"

    def form_valid(self, form):
        if not self.request.user.establecimiento:
            messages.error(
                self.request,
                "Su usuario no tiene un establecimiento de salud asignado. No puede crear solicitudes de códigos."
            )
            return self.form_invalid(form)

        solicitud = form.save(commit=False)
        solicitud.usuario_solicitante = self.request.user
        solicitud.establecimiento = self.request.user.establecimiento
        solicitud.estado = SolicitudCodigo.ESTADO_PENDIENTE_VALIDACION
        solicitud.numero_solicitud = solicitud.generar_folio()
        solicitud.created_by = self.request.user
        solicitud.save()

        # Registrar evento en la trazabilidad
        solicitud.registrar_evento(
            usuario=self.request.user,
            accion="Creación de Solicitud",
            estado_anterior=None,
            estado_nuevo=solicitud.estado,
            detalle=f"Ingreso de requerimiento para {solicitud.producto_base}. Folio generado: {solicitud.numero_solicitud}."
        )

        messages.success(
            self.request,
            f"Solicitud {solicitud.numero_solicitud} registrada con éxito. Se encuentra pendiente de validación por el referente."
        )
        return redirect("solicitud_codigo:detalle", pk=solicitud.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_title"] = "Nueva Solicitud de Código SISSA"
        return context


# ==============================================================================
# 5. DETALLE COMPLETO DE LA SOLICITUD
# ==============================================================================
class SolicitudDetailView(LoginRequiredMixin, DetailView):
    model = SolicitudCodigo
    template_name = "solicitud_codigo/solicitud_detalle.html"
    context_object_name = "solicitud"

    def get_object(self, queryset=None):
        solicitud = super().get_object(queryset)
        user = self.request.user

        es_solicitante = (solicitud.usuario_solicitante_id == user.id)
        es_referente_autorizado = user_can_manage_solicitud(user, solicitud)
        es_creador = user_can_create_codes(user)

        # Si el usuario es referente de otra área o un usuario normal ajeno, denegar
        if not (es_solicitante or es_referente_autorizado or es_creador):
            raise PermissionDenied("No tiene autorización para visualizar los antecedentes de esta solicitud.")

        return solicitud

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sol = self.object
        user = self.request.user

        context["view_title"] = f"Solicitud {sol.numero_solicitud or sol.id}"
        context["historial"] = sol.historial_eventos.all().order_by("fecha", "id")

        # Permisos contextuales según estado y rol del usuario
        context["puede_corregir"] = sol.puede_ser_editada_por(user)
        context["puede_gestionar_referente"] = (
            user_can_manage_solicitud(user, sol) and sol.estado == SolicitudCodigo.ESTADO_PENDIENTE_VALIDACION
        )
        context["puede_crear_codigo"] = (
            user_can_create_codes(user) and sol.estado in [
                SolicitudCodigo.ESTADO_VALIDADA,
                SolicitudCodigo.ESTADO_PENDIENTE_CREACION,
            ]
        )

        # Formularios para acciones modales
        context["form_observar"] = ObservarSolicitudForm()
        context["form_rechazar"] = RechazarSolicitudForm()
        context["form_validar"] = ValidarSolicitudForm()
        context["form_crear_codigo"] = CrearCodigoEfectivoForm(initial={
            "codigo_creado": "",
            "observaciones_creacion": f"Resolución de solicitud {sol.numero_solicitud} para {sol.producto_base} ({sol.presentacion})."
        })

        return context


# ==============================================================================
# 6. CORRECCIÓN Y REENVÍO DE SOLICITUD OBSERVADA
# ==============================================================================
class SolicitudCorregirView(LoginRequiredMixin, UpdateView):
    model = SolicitudCodigo
    form_class = SolicitudCodigoCorregirForm
    template_name = "solicitud_codigo/solicitud_corregir.html"
    context_object_name = "solicitud"

    def dispatch(self, request, *args, **kwargs):
        sol = self.get_object()
        if not sol.puede_ser_editada_por(request.user):
            messages.error(
                request,
                "Esta solicitud no se encuentra en estado 'Observada' o usted no es el solicitante autorizado."
            )
            return redirect("solicitud_codigo:detalle", pk=sol.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        solicitud = form.save(commit=False)
        solicitud.estado = SolicitudCodigo.ESTADO_PENDIENTE_VALIDACION
        solicitud.fecha_reenvio = timezone.now()
        solicitud.updated_by = self.request.user
        solicitud.save()

        # Registrar evento en la trazabilidad
        solicitud.registrar_evento(
            usuario=self.request.user,
            accion="Reenvío tras Corrección",
            estado_anterior=SolicitudCodigo.ESTADO_OBSERVADA,
            estado_nuevo=solicitud.estado,
            detalle="Solicitud subsanada por el solicitante y reenviada para nueva revisión del referente."
        )

        messages.success(
            self.request,
            f"Solicitud {solicitud.numero_solicitud} corregida y reenviada con éxito para validación."
        )
        return redirect("solicitud_codigo:detalle", pk=solicitud.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_title"] = f"Corregir Solicitud {self.object.numero_solicitud}"
        return context


# ==============================================================================
# 7. ACCIONES DE GESTIÓN DEL REFERENTE (OBSERVAR, RECHAZAR, VALIDAR)
# ==============================================================================
class SolicitudObservarView(ReferenteRequiredMixin, View):
    def post(self, request, pk):
        solicitud = get_object_or_404(SolicitudCodigo, pk=pk, is_active=True)

        if not user_can_manage_solicitud(request.user, solicitud):
            raise PermissionDenied("No tiene autorización sobre el área de esta solicitud.")

        if solicitud.estado != SolicitudCodigo.ESTADO_PENDIENTE_VALIDACION:
            messages.error(request, "Solo se pueden observar solicitudes en estado 'Pendiente de Validación'.")
            return redirect("solicitud_codigo:detalle", pk=solicitud.pk)

        form = ObservarSolicitudForm(request.POST)
        if form.is_valid():
            observaciones = form.cleaned_data["observaciones"]
            estado_anterior = solicitud.estado

            solicitud.estado = SolicitudCodigo.ESTADO_OBSERVADA
            solicitud.observaciones_referente = observaciones
            solicitud.fecha_observacion = timezone.now()
            solicitud.usuario_referente = request.user
            solicitud.updated_by = request.user
            solicitud.save()

            solicitud.registrar_evento(
                usuario=request.user,
                accion="Solicitud Observada",
                estado_anterior=estado_anterior,
                estado_nuevo=solicitud.estado,
                detalle=f"Observaciones del referente: {observaciones}"
            )

            messages.warning(
                request,
                f"Solicitud {solicitud.numero_solicitud} devuelta al solicitante con observaciones."
            )
        else:
            messages.error(request, "Debe ingresar una justificación detallada para observar la solicitud.")

        return redirect("solicitud_codigo:detalle", pk=solicitud.pk)


class SolicitudRechazarView(ReferenteRequiredMixin, View):
    def post(self, request, pk):
        solicitud = get_object_or_404(SolicitudCodigo, pk=pk, is_active=True)

        if not user_can_manage_solicitud(request.user, solicitud):
            raise PermissionDenied("No tiene autorización sobre el área de esta solicitud.")

        if solicitud.estado != SolicitudCodigo.ESTADO_PENDIENTE_VALIDACION:
            messages.error(request, "Solo se pueden rechazar solicitudes en estado 'Pendiente de Validación'.")
            return redirect("solicitud_codigo:detalle", pk=solicitud.pk)

        form = RechazarSolicitudForm(request.POST)
        if form.is_valid():
            motivo = form.cleaned_data["motivo_rechazo"]
            estado_anterior = solicitud.estado

            solicitud.estado = SolicitudCodigo.ESTADO_RECHAZADA
            solicitud.motivo_rechazo = motivo
            solicitud.fecha_rechazo = timezone.now()
            solicitud.usuario_referente = request.user
            solicitud.updated_by = request.user
            solicitud.save()

            solicitud.registrar_evento(
                usuario=request.user,
                accion="Solicitud Rechazada",
                estado_anterior=estado_anterior,
                estado_nuevo=solicitud.estado,
                detalle=f"Motivo de rechazo: {motivo}"
            )

            messages.error(
                request,
                f"Solicitud {solicitud.numero_solicitud} rechazada."
            )
        else:
            messages.error(request, "Debe ingresar un motivo fundado para rechazar la solicitud.")

        return redirect("solicitud_codigo:detalle", pk=solicitud.pk)


class SolicitudValidarView(ReferenteRequiredMixin, View):
    def post(self, request, pk):
        solicitud = get_object_or_404(SolicitudCodigo, pk=pk, is_active=True)

        if not user_can_manage_solicitud(request.user, solicitud):
            raise PermissionDenied("No tiene autorización sobre el área de esta solicitud.")

        if solicitud.estado != SolicitudCodigo.ESTADO_PENDIENTE_VALIDACION:
            messages.error(request, "Solo se pueden validar solicitudes en estado 'Pendiente de Validación'.")
            return redirect("solicitud_codigo:detalle", pk=solicitud.pk)

        form = ValidarSolicitudForm(request.POST)
        comentarios = ""
        if form.is_valid():
            comentarios = form.cleaned_data.get("observaciones", "").strip()

        estado_anterior = solicitud.estado
        solicitud.estado = SolicitudCodigo.ESTADO_VALIDADA
        solicitud.fecha_validacion = timezone.now()
        solicitud.usuario_referente = request.user
        solicitud.updated_by = request.user
        if comentarios:
            solicitud.observaciones_referente = comentarios
        solicitud.save()

        solicitud.registrar_evento(
            usuario=request.user,
            accion="Validación de Solicitud",
            estado_anterior=estado_anterior,
            estado_nuevo=solicitud.estado,
            detalle=f"Solicitud validada técnicamente. {comentarios}".strip()
        )

        messages.success(
            request,
            f"Solicitud {solicitud.numero_solicitud} validada exitosamente. Queda pendiente para creación efectiva de código."
        )
        return redirect("solicitud_codigo:detalle", pk=solicitud.pk)


# ==============================================================================
# 8. REGISTRO DE CREACIÓN EFECTIVA Y CIERRE DE SOLICITUD
# ==============================================================================
class SolicitudCrearCodigoView(CreadorCodigoRequiredMixin, View):
    def post(self, request, pk):
        solicitud = get_object_or_404(SolicitudCodigo, pk=pk, is_active=True)

        if solicitud.estado not in [
            SolicitudCodigo.ESTADO_VALIDADA,
            SolicitudCodigo.ESTADO_PENDIENTE_CREACION,
        ]:
            messages.error(
                request,
                "Solo se puede registrar código en solicitudes 'Validadas' o 'Pendientes de Creación'."
            )
            return redirect("solicitud_codigo:detalle", pk=solicitud.pk)

        form = CrearCodigoEfectivoForm(request.POST)
        if form.is_valid():
            codigo = form.cleaned_data["codigo_creado"].strip().upper()
            obs = form.cleaned_data.get("observaciones_creacion", "").strip()
            registrar_en_maestra = form.cleaned_data.get("registrar_en_maestra", False)

            estado_anterior = solicitud.estado
            solicitud.estado = SolicitudCodigo.ESTADO_CODIGO_CREADO
            solicitud.codigo_creado = codigo
            solicitud.observaciones_creacion = obs
            solicitud.fecha_creacion_codigo = timezone.now()
            solicitud.usuario_creador_codigo = request.user
            solicitud.updated_by = request.user
            solicitud.save()

            if registrar_en_maestra:
                MaestraCodigoSISSA.objects.get_or_create(
                    codigo=codigo,
                    defaults={
                        "nombre_producto": solicitud.producto_base,
                        "presentacion": solicitud.presentacion,
                        "descripcion": solicitud.descripcion_requerimiento,
                        "area": solicitud.area,
                        "subarea": solicitud.subarea,
                        "created_by": request.user,
                    }
                )

            solicitud.registrar_evento(
                usuario=request.user,
                accion="Código SISSA Creado",
                estado_anterior=estado_anterior,
                estado_nuevo=solicitud.estado,
                detalle=f"Se registró código SISSA asignado: '{codigo}'. {obs}".strip()
            )

            messages.success(
                request,
                f"Código {codigo} registrado exitosamente. La solicitud {solicitud.numero_solicitud} ha sido resuelta."
            )
        else:
            messages.error(request, "Debe ingresar un código SISSA válido.")

        return redirect("solicitud_codigo:detalle", pk=solicitud.pk)


# ==============================================================================
# 9. ENDPOINTS AJAX AUXILIARES (SUBAREAS Y COINCIDENCIAS)
# ==============================================================================
class SubareasPorAreaAPIView(LoginRequiredMixin, View):
    def get(self, request):
        area_id = request.GET.get("area_id")
        if not area_id:
            return JsonResponse({"subareas": []})

        try:
            subareas = SubareaSolicitud.objects.filter(
                area_id=int(area_id), is_active=True
            ).order_by("nombre").values("id", "nombre", "codigo")
            return JsonResponse({"subareas": list(subareas)})
        except (ValueError, TypeError):
            return JsonResponse({"subareas": []})


class BuscarCoincidenciasAPIView(LoginRequiredMixin, View):
    def get(self, request):
        query = request.GET.get("q", "").strip()
        area_id = request.GET.get("area_id")

        if len(query) < 2:
            return JsonResponse({"coincidencias": [], "total": 0})

        resultados = []
        vistos = set()

        # 1. Buscar en MaestraCodigoSISSA
        maestra_qs = MaestraCodigoSISSA.objects.filter(is_active=True)
        if area_id:
            try:
                maestra_qs = maestra_qs.filter(Q(area_id=int(area_id)) | Q(area__isnull=True))
            except (ValueError, TypeError):
                pass

        maestra_filtro = (
            Q(codigo__icontains=query) |
            Q(nombre_producto__icontains=query) |
            Q(presentacion__icontains=query) |
            Q(descripcion__icontains=query)
        )

        for item in maestra_qs.filter(maestra_filtro)[:15]:
            clave = item.codigo.upper()
            if clave not in vistos:
                vistos.add(clave)
                resultados.append({
                    "codigo": item.codigo,
                    "nombre": item.nombre_producto,
                    "presentacion": item.presentacion or "—",
                    "area": item.area.nombre if item.area else "General",
                    "origen": "Maestra SISSA",
                })

        # 2. Buscar en Catálogo Bodega (Producto)
        bodega_filtro = Q(codigo__icontains=query) | Q(nombre__icontains=query) | Q(descripcion__icontains=query)
        for prod in Producto.objects.filter(bodega_filtro, is_active=True)[:15]:
            if prod.codigo:
                clave = prod.codigo.upper()
                if clave not in vistos:
                    vistos.add(clave)
                    resultados.append({
                        "codigo": prod.codigo,
                        "nombre": prod.nombre,
                        "presentacion": str(prod.unidad_medida) if prod.unidad_medida else "—",
                        "area": str(prod.categoria) if prod.categoria else "Bodega",
                        "origen": "Catálogo Productos",
                    })

        # 3. Buscar en Solicitudes ya resueltas con código creado
        sol_qs = SolicitudCodigo.objects.filter(
            is_active=True,
            estado=SolicitudCodigo.ESTADO_CODIGO_CREADO,
            codigo_creado__isnull=False
        ).exclude(codigo_creado="")

        sol_filtro = (
            Q(codigo_creado__icontains=query) |
            Q(producto_base__icontains=query) |
            Q(presentacion__icontains=query)
        )

        for sol in sol_qs.filter(sol_filtro)[:10]:
            if sol.codigo_creado:
                clave = sol.codigo_creado.upper()
                if clave not in vistos:
                    vistos.add(clave)
                    resultados.append({
                        "codigo": sol.codigo_creado,
                        "nombre": sol.producto_base,
                        "presentacion": sol.presentacion or "—",
                        "area": sol.area.nombre if sol.area else "General",
                        "origen": "Solicitud Previa Resuelta",
                    })

        return JsonResponse({
            "coincidencias": resultados,
            "total": len(resultados),
        })
