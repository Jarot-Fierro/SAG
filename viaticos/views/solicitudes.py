from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone

from core.standard.views import (
    StandardListView,
    StandardCreateView,
    StandardUpdateView,
    StandardDetailView,
)
from ..filters.solicitud import FiltroMisSolicitudes, FiltroSolicitud
from ..forms.solicitud import SolicitudCometidoViaticoForm, ItinerarioDestinoForm, CalculoViaticoForm
from ..models.catalogos import EscalaViatico
from ..models.solicitud import SolicitudCometidoViatico, ItinerarioDestino, CalculoViatico

MODULE_NAME = 'Solicitudes de Viáticos'


# ----------------------------------------------------
# 1. Solicitudes Generales
# ----------------------------------------------------

class SolicitudListView(StandardListView):
    model = SolicitudCometidoViatico
    filter_form_class = FiltroSolicitud
    template_name = "viaticos/solicitudes/solicitud_list.html"
    title = "Gestión de Cometidos y Viáticos"

    list_url_name = "viaticos:solicitud_list"
    create_url_name = "viaticos:solicitud_create"
    update_url_name = "viaticos:solicitud_update"
    delete_url_name = "viaticos:solicitud_delete"

    def get_queryset(self):
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
        ).select_related(
            "funcionario",
            "unidad_organizacional",
            "establecimiento"
        )

        if (
                not self.request.user.is_superuser
                and hasattr(self.request.user, 'establecimiento')
        ):
            queryset = queryset.filter(
                establecimiento=self.request.user.establecimiento
            )

        if self.filter_form and self.filter_form.is_valid():
            data = self.filter_form.cleaned_data

            if data.get("folio"):
                queryset = queryset.filter(
                    folio=data["folio"]
                )

            if data.get("funcionario"):
                queryset = queryset.filter(
                    funcionario__nombres__icontains=data["funcionario"]
                )

            if data.get("es_urgente"):
                queryset = queryset.filter(
                    es_urgente=(data["es_urgente"] == '1')
                )

            if data.get("etapa"):
                etapa_map = {
                    'JEFE_DIRECTO': 'ENVIADO_JEFATURA',
                    'SERVICIOS_GENERALES': 'EN_REVISION_SSGG',
                    'RRHH_CONTROL': 'EN_REVISION_RRHH',
                    'EN_PAGO': 'EN_PAGO',
                }

                estado_target = etapa_map.get(data["etapa"])

                if estado_target:
                    queryset = queryset.filter(
                        estado=estado_target
                    )

        return queryset


class MisSolicitudesListView(StandardListView):
    model = SolicitudCometidoViatico
    filter_form_class = FiltroMisSolicitudes
    template_name = "viaticos/solicitudes/mis_solicitudes_list.html"
    title = "Mis Cometidos y Viáticos"

    list_url_name = "viaticos:mis_solicitudes_list"
    create_url_name = "viaticos:solicitud_create"
    update_url_name = "viaticos:solicitud_update"
    delete_url_name = "viaticos:solicitud_delete"

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            "funcionario", "unidad_organizacional"
        )

        # Filtrar solo las solicitudes del funcionario actual o creadas por el usuario
        if hasattr(self.request.user, 'funcionario') and self.request.user.funcionario:
            queryset = queryset.filter(funcionario=self.request.user.funcionario)
        else:
            queryset = queryset.filter(created_by=self.request.user)

        if self.filter_form and self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data.get("folio"):
                queryset = queryset.filter(folio=data["folio"])
            if data.get("ano"):
                queryset = queryset.filter(ano=data["ano"])
            if data.get("tipo_solicitud"):
                queryset = queryset.filter(tipo_solicitud=data["tipo_solicitud"])
            if data.get("estado"):
                queryset = queryset.filter(estado=data["estado"])
            if data.get("fecha_desde"):
                queryset = queryset.filter(fecha_inicio__gte=data["fecha_desde"])
            if data.get("fecha_hasta"):
                queryset = queryset.filter(fecha_termino__lte=data["fecha_hasta"])

        return queryset


class SolicitudCreateView(StandardCreateView):
    model = SolicitudCometidoViatico
    form_class = SolicitudCometidoViaticoForm
    template_name = "viaticos/solicitudes/solicitud_form.html"
    title = "Nueva Solicitud de Cometido / Viático"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        current_year = timezone.now().year
        form.instance.ano = current_year
        form.instance.estado = 'BORRADOR'

        # Asignar establecimiento
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            form.instance.establecimiento = self.request.user.establecimiento

        # Calcular folio correlativo único por año y establecimiento
        with transaction.atomic():
            max_folio = SolicitudCometidoViatico.objects.filter(
                ano=current_year,
                establecimiento=form.instance.establecimiento
            ).aggregate(Max('folio'))['folio__max'] or 0
            form.instance.folio = max_folio + 1

            response = super().form_valid(form)

            # Intentar generar cálculo financiero inicial si aplica viático
            if form.instance.tipo_solicitud == 'COMETIDO_VIATICO':
                escala = EscalaViatico.objects.filter(
                    ano_vigencia=current_year, is_active=True
                ).first()
                if escala:
                    CalculoViatico.objects.get_or_create(
                        solicitud=form.instance,
                        defaults={
                            'escala_aplicada': escala,
                            'dias_100': 0,
                            'monto_unitario_100': escala.valor_100_pernocta,
                            'dias_50': 0,
                            'monto_unitario_50': escala.valor_50_parcial,
                            'dias_faena': 0,
                            'monto_unitario_faena': escala.valor_faena,
                            'total_bruto_viatico': 0,
                            'saldo_a_pagar': 0,
                        }
                    )

            return response

    def get_success_url(self):
        return reverse('viaticos:solicitud_detail', kwargs={'pk': self.object.pk})


class SolicitudUpdateView(StandardUpdateView):
    model = SolicitudCometidoViatico
    form_class = SolicitudCometidoViaticoForm
    template_name = "viaticos/solicitudes/solicitud_form.html"
    title = "Editar Solicitud de Cometido / Viático"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        return reverse('viaticos:solicitud_detail', kwargs={'pk': self.object.pk})


class SolicitudDetailView(StandardDetailView):
    model = SolicitudCometidoViatico
    template_name = "viaticos/solicitudes/solicitud_detail.html"
    title = "Detalle de Solicitud de Cometido y Viático"
    module_name = MODULE_NAME

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        solicitud = self.get_object()
        context['solicitud'] = solicitud
        context['itinerarios'] = solicitud.itinerarios.filter(is_active=True).select_related('lugar_destino')
        context['calculo'] = getattr(solicitud, 'calculo_financiero', None)
        context['gastos_transporte'] = solicitud.gastos_transporte.filter(is_active=True)
        context['aprobaciones'] = solicitud.historial_aprobaciones.all().select_related('usuario_firmante')
        context['resolucion'] = getattr(solicitud, 'resolucion_formal', None)
        context['egresos'] = solicitud.egresos_pago.filter(is_active=True)
        context['rendicion'] = getattr(solicitud, 'rendicion_cuentas', None)
        return context


@login_required
def solicitud_delete(request, pk):
    filter_kwargs = {'pk': pk}
    if not request.user.is_superuser and hasattr(SolicitudCometidoViatico, 'establecimiento'):
        filter_kwargs['establecimiento'] = request.user.establecimiento

    solicitud = get_object_or_404(SolicitudCometidoViatico, **filter_kwargs)
    solicitud.is_active = False
    solicitud.save()
    messages.success(request, f'Solicitud Folio {solicitud.folio}/{solicitud.ano} desactivada correctamente.')
    return redirect('viaticos:solicitud_list')


@login_required
def solicitud_enviar_jefatura(request, pk):
    filter_kwargs = {'pk': pk}
    if not request.user.is_superuser and hasattr(SolicitudCometidoViatico, 'establecimiento'):
        filter_kwargs['establecimiento'] = request.user.establecimiento

    solicitud = get_object_or_404(SolicitudCometidoViatico, **filter_kwargs)
    if solicitud.estado in ['BORRADOR', 'DEVUELTO']:
        solicitud.estado = 'ENVIADO_JEFATURA'
        solicitud.save()
        messages.success(request, f'Solicitud Folio {solicitud.folio} enviada exitosamente a Jefatura Directa.')
    else:
        messages.warning(request, f'La solicitud no se encuentra en estado Borrador o Devuelto.')
    return redirect('viaticos:solicitud_detail', pk=solicitud.pk)


@login_required
def solicitud_anular(request, pk):
    filter_kwargs = {'pk': pk}
    if not request.user.is_superuser and hasattr(SolicitudCometidoViatico, 'establecimiento'):
        filter_kwargs['establecimiento'] = request.user.establecimiento

    solicitud = get_object_or_404(SolicitudCometidoViatico, **filter_kwargs)
    solicitud.estado = 'ANULADO'
    solicitud.save()
    messages.warning(request, f'Solicitud Folio {solicitud.folio}/{solicitud.ano} anulada correctamente.')
    return redirect('viaticos:solicitud_detail', pk=solicitud.pk)


# ----------------------------------------------------
# 2. Itinerarios (Tramos de Destino)
# ----------------------------------------------------

class ItinerarioCreateView(StandardCreateView):
    model = ItinerarioDestino
    form_class = ItinerarioDestinoForm
    template_name = "viaticos/solicitudes/itinerario_form.html"
    title = "Agregar Tramo al Itinerario"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        solicitud_id = self.kwargs.get('solicitud_id')
        solicitud = get_object_or_404(SolicitudCometidoViatico, pk=solicitud_id)
        form.instance.solicitud = solicitud
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('viaticos:solicitud_detail', kwargs={'pk': self.kwargs.get('solicitud_id')})


class ItinerarioUpdateView(StandardUpdateView):
    model = ItinerarioDestino
    form_class = ItinerarioDestinoForm
    template_name = "viaticos/solicitudes/itinerario_form.html"
    title = "Editar Tramo de Itinerario"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        return reverse('viaticos:solicitud_detail', kwargs={'pk': self.object.solicitud.pk})


@login_required
def itinerario_delete(request, pk):
    itinerario = get_object_or_404(ItinerarioDestino, pk=pk)
    solicitud_id = itinerario.solicitud.pk
    itinerario.is_active = False
    itinerario.save()
    messages.success(request, 'Tramo de itinerario eliminado correctamente.')
    return redirect('viaticos:solicitud_detail', pk=solicitud_id)


# ----------------------------------------------------
# 3. Cálculo y Liquidación Financiera
# ----------------------------------------------------

class CalculoViaticoUpdateView(StandardUpdateView):
    model = CalculoViatico
    form_class = CalculoViaticoForm
    template_name = "viaticos/solicitudes/calculo_form.html"
    title = "Cálculo y Liquidación de Viático"
    module_name = MODULE_NAME

    def get_success_url(self):
        return reverse('viaticos:solicitud_detail', kwargs={'pk': self.object.solicitud.pk})
