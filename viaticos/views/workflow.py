from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone

from core.standard.views import (
    StandardListView,
    StandardCreateView,
)
from ..filters.workflow import FiltroAprobacionCometido, FiltroBandejaFirmas
from ..forms.workflow import AprobacionCometidoForm
from ..models.solicitud import SolicitudCometidoViatico
from ..models.wokflow import AprobacionCometido

MODULE_NAME = 'Flujo de Firmas y Aprobaciones'


class BandejaFirmasListView(StandardListView):
    model = SolicitudCometidoViatico
    filter_form_class = FiltroBandejaFirmas
    template_name = "viaticos/workflow/bandeja_firmas_list.html"
    title = "Bandeja de Autorizaciones y Firmas Pendientes"

    list_url_name = "viaticos:bandeja_firmas"
    create_url_name = "viaticos:solicitud_create"
    update_url_name = "viaticos:solicitud_detail"
    delete_url_name = "viaticos:solicitud_detail"

    def get_queryset(self):
        # Solicitudes en etapas de revisión y firma
        self.filter_form = self.get_filter_form()
        queryset = SolicitudCometidoViatico.objects.filter(
            estado__in=[
                'ENVIADO_JEFATURA',
                'EN_REVISION_SSGG',
                'EN_REVISION_RRHH',
                'RESOLUCION_EMITIDA',
                'EN_PAGO'
            ],
            is_active=True
        ).select_related("funcionario", "unidad_organizacional", "establecimiento")

        if not self.request.user.is_superuser and hasattr(self.request.user, 'establecimiento'):
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)

        if self.filter_form and self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data.get("folio"):
                queryset = queryset.filter(folio=data["folio"])
            if data.get("funcionario"):
                queryset = queryset.filter(funcionario__nombres__icontains=data["funcionario"])
            if data.get("es_urgente"):
                queryset = queryset.filter(es_urgente=(data["es_urgente"] == '1'))
            if data.get("etapa"):
                etapa_map = {
                    'JEFE_DIRECTO': 'ENVIADO_JEFATURA',
                    'SERVICIOS_GENERALES': 'EN_REVISION_SSGG',
                    'RRHH_CONTROL': 'EN_REVISION_RRHH',
                    'EN_PAGO': 'EN_PAGO',
                }
                estado_target = etapa_map.get(data["etapa"])
                if estado_target:
                    queryset = queryset.filter(estado=estado_target)

        return queryset


class AprobacionCometidoCreateView(StandardCreateView):
    model = AprobacionCometido
    form_class = AprobacionCometidoForm
    template_name = "viaticos/workflow/aprobacion_form.html"
    title = "Revisión y Firma de Solicitud"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        solicitud_id = self.kwargs.get('solicitud_id')
        context['solicitud'] = get_object_or_404(SolicitudCometidoViatico, pk=solicitud_id)
        return context

    def form_valid(self, form):
        solicitud_id = self.kwargs.get('solicitud_id')
        solicitud = get_object_or_404(SolicitudCometidoViatico, pk=solicitud_id)

        form.instance.solicitud = solicitud
        form.instance.usuario_firmante = self.request.user

        # Capturar IP si es posible
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        form.instance.ip_registro = ip

        # Máquina de estados según etapa y acción
        accion = form.cleaned_data['accion']
        etapa = form.cleaned_data['etapa']

        if accion == 'APROBADO' or accion == 'SUBROGADO':
            if etapa == 'JEFE_DIRECTO':
                solicitud.fecha_aprobacion_jefe = timezone.now()
                if solicitud.requiere_vehiculo_institucional or solicitud.tiene_derecho_pasaje or solicitud.requiere_vales_bencina:
                    solicitud.estado = 'EN_REVISION_SSGG'
                else:
                    solicitud.estado = 'EN_REVISION_RRHH'
            elif etapa == 'SERVICIOS_GENERALES':
                solicitud.estado = 'EN_REVISION_RRHH'
            elif etapa == 'RRHH_CONTROL':
                solicitud.fecha_aprobacion_rrhh = timezone.now()
                solicitud.estado = 'RESOLUCION_EMITIDA'
            elif etapa == 'DIRECCION_FIRMA':
                solicitud.estado = 'EN_PAGO'
            elif etapa == 'FINANZAS_PAGO':
                solicitud.estado = 'PAGADO'
                solicitud.fecha_pago = timezone.now().date()
        elif accion == 'DEVUELTO':
            solicitud.estado = 'DEVUELTO'
            solicitud.motivo_rechazo_devolucion = form.cleaned_data.get('observaciones')
        elif accion == 'RECHAZADO':
            solicitud.estado = 'RECHAZADO'
            solicitud.motivo_rechazo_devolucion = form.cleaned_data.get('observaciones')

        solicitud.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('viaticos:solicitud_detail', kwargs={'pk': self.kwargs.get('solicitud_id')})


class HistorialFirmasListView(StandardListView):
    model = AprobacionCometido
    filter_form_class = FiltroAprobacionCometido
    template_name = "viaticos/workflow/historial_firmas_list.html"
    title = "Historial y Registro de Firmas de Cometidos"

    list_url_name = "viaticos:historial_firmas"
    create_url_name = "viaticos:bandeja_firmas"
    update_url_name = "viaticos:solicitud_detail"
    delete_url_name = "viaticos:solicitud_detail"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("solicitud", "usuario_firmante", "solicitud__funcionario")

        if not self.request.user.is_superuser and hasattr(self.request.user, 'establecimiento'):
            queryset = queryset.filter(solicitud__establecimiento=self.request.user.establecimiento)

        if self.filter_form and self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data.get("etapa"):
                queryset = queryset.filter(etapa=data["etapa"])
            if data.get("accion"):
                queryset = queryset.filter(accion=data["accion"])
            if data.get("firmante"):
                queryset = queryset.filter(usuario_firmante__username__icontains=data["firmante"])
            if data.get("fecha_desde"):
                queryset = queryset.filter(fecha_hora_accion__date__gte=data["fecha_desde"])
            if data.get("fecha_hasta"):
                queryset = queryset.filter(fecha_hora_accion__date__lte=data["fecha_hasta"])

        return queryset
