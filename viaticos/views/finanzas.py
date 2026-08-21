from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone

from core.standard.views import (
    StandardListView,
    StandardCreateView,
    StandardUpdateView,
    StandardDetailView,
)
from ..filters.finanzas import FiltroEgresoPagoViatico, FiltroRendicionCometido
from ..forms.finanzas import EgresoPagoViaticoForm, RendicionCometidoForm, DetalleRendicionGastoForm
from ..models.finanzas import EgresoPagoViatico, RendicionCometido, DetalleRendicionGasto
from ..models.solicitud import SolicitudCometidoViatico

MODULE_NAME = 'Finanzas y Rendición de Cuentas'


# ----------------------------------------------------
# 1. Egresos y Pagos
# ----------------------------------------------------

class EgresoPagoViaticoListView(StandardListView):
    model = EgresoPagoViatico
    filter_form_class = FiltroEgresoPagoViatico
    template_name = "viaticos/finanzas/egreso_list.html"
    title = "Egresos y Pagos de Viáticos"

    list_url_name = "viaticos:egreso_list"
    create_url_name = "viaticos:egreso_create"
    update_url_name = "viaticos:egreso_update"
    delete_url_name = "viaticos:egreso_delete"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("solicitud", "solicitud__funcionario")

        if not self.request.user.is_superuser and hasattr(self.request.user, 'establecimiento'):
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)

        if self.filter_form and self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data.get("numero_egreso"):
                queryset = queryset.filter(numero_egreso=data["numero_egreso"])
            if data.get("ano_egreso"):
                queryset = queryset.filter(ano_egreso=data["ano_egreso"])
            if data.get("medio_pago"):
                queryset = queryset.filter(medio_pago=data["medio_pago"])
            if data.get("beneficiario"):
                queryset = queryset.filter(nombre_beneficiario__icontains=data["beneficiario"])
            if data.get("fecha_desde"):
                queryset = queryset.filter(fecha_pago__gte=data["fecha_desde"])
            if data.get("fecha_hasta"):
                queryset = queryset.filter(fecha_pago__lte=data["fecha_hasta"])

        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class EgresoPagoViaticoCreateView(StandardCreateView):
    model = EgresoPagoViatico
    form_class = EgresoPagoViaticoForm
    template_name = "viaticos/finanzas/egreso_form.html"
    title = "Registrar Egreso y Pago de Viático"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        solicitud_id = self.request.GET.get('solicitud')
        if solicitud_id:
            solicitud = SolicitudCometidoViatico.objects.filter(pk=solicitud_id).first()
            if solicitud:
                initial['solicitud'] = solicitud
                initial['fecha_pago'] = timezone.now().date()
                if hasattr(solicitud, 'calculo_financiero') and solicitud.calculo_financiero:
                    initial['monto_total_pagado'] = solicitud.calculo_financiero.saldo_a_pagar
                if solicitud.funcionario:
                    initial['nombre_beneficiario'] = str(solicitud.funcionario)
                    if hasattr(solicitud.funcionario, 'rut'):
                        initial['rut_beneficiario'] = solicitud.funcionario.rut
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.solicitud.estado = 'PAGADO'
        self.object.solicitud.fecha_pago = self.object.fecha_pago
        self.object.solicitud.save()
        return response

    def get_success_url(self):
        return reverse('viaticos:solicitud_detail', kwargs={'pk': self.object.solicitud.pk})


class EgresoPagoViaticoUpdateView(StandardUpdateView):
    model = EgresoPagoViatico
    form_class = EgresoPagoViaticoForm
    template_name = "viaticos/finanzas/egreso_form.html"
    title = "Editar Registro de Egreso y Pago"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        return reverse('viaticos:solicitud_detail', kwargs={'pk': self.object.solicitud.pk})


class EgresoPagoViaticoDetailView(StandardDetailView):
    model = EgresoPagoViatico
    title = "Detalle de Egreso Presupuestario"
    module_name = MODULE_NAME


@login_required
def egreso_pago_delete(request, pk):
    egreso = get_object_or_404(EgresoPagoViatico, pk=pk)
    egreso.is_active = False
    egreso.save()
    messages.success(request, f'Egreso N° {egreso.numero_egreso}/{egreso.ano_egreso} desactivado correctamente.')
    return redirect('viaticos:egreso_list')


# ----------------------------------------------------
# 2. Rendición de Cuentas
# ----------------------------------------------------

class RendicionCometidoListView(StandardListView):
    model = RendicionCometido
    filter_form_class = FiltroRendicionCometido
    template_name = "viaticos/finanzas/rendicion_list.html"
    title = "Rendiciones de Cometidos y Cuentas"

    list_url_name = "viaticos:rendicion_list"
    create_url_name = "viaticos:rendicion_create"
    update_url_name = "viaticos:rendicion_update"
    delete_url_name = "viaticos:rendicion_list"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("solicitud", "solicitud__funcionario")

        if not self.request.user.is_superuser and hasattr(self.request.user, 'establecimiento'):
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)

        if self.filter_form and self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data.get("folio_solicitud"):
                queryset = queryset.filter(solicitud__folio=data["folio_solicitud"])
            if data.get("rendicion_aprobada"):
                queryset = queryset.filter(rendicion_aprobada=(data["rendicion_aprobada"] == '1'))
            if data.get("fecha_desde"):
                queryset = queryset.filter(fecha_rendicion__gte=data["fecha_desde"])
            if data.get("fecha_hasta"):
                queryset = queryset.filter(fecha_rendicion__lte=data["fecha_hasta"])

        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class RendicionCometidoCreateView(StandardCreateView):
    model = RendicionCometido
    form_class = RendicionCometidoForm
    template_name = "viaticos/finanzas/rendicion_form.html"
    title = "Crear Rendición de Cometido"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        solicitud_id = self.request.GET.get('solicitud')
        if solicitud_id:
            solicitud = SolicitudCometidoViatico.objects.filter(pk=solicitud_id).first()
            if solicitud:
                initial['solicitud'] = solicitud
                initial['fecha_rendicion'] = timezone.now().date()
                if hasattr(solicitud, 'calculo_financiero') and solicitud.calculo_financiero:
                    initial['total_anticipo_recibido'] = solicitud.calculo_financiero.monto_anticipo_entregado
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.solicitud.estado = 'RENDIDO'
        self.object.solicitud.save()
        return response

    def get_success_url(self):
        return reverse('viaticos:solicitud_detail', kwargs={'pk': self.object.solicitud.pk})


class RendicionCometidoUpdateView(StandardUpdateView):
    model = RendicionCometido
    form_class = RendicionCometidoForm
    template_name = "viaticos/finanzas/rendicion_form.html"
    title = "Editar Rendición de Cometido"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        return reverse('viaticos:solicitud_detail', kwargs={'pk': self.object.solicitud.pk})


class RendicionCometidoDetailView(StandardDetailView):
    model = RendicionCometido
    title = "Detalle de Rendición de Cuentas"
    module_name = MODULE_NAME

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rendicion = self.get_object()
        context['detalles_gasto'] = rendicion.detalles_gasto.filter(is_active=True)
        return context


# ----------------------------------------------------
# 3. Detalle de Gastos Rendidos
# ----------------------------------------------------

class DetalleRendicionGastoCreateView(StandardCreateView):
    model = DetalleRendicionGasto
    form_class = DetalleRendicionGastoForm
    template_name = "viaticos/finanzas/detalle_gasto_form.html"
    title = "Agregar Comprobante de Gasto a Rendición"
    module_name = MODULE_NAME

    def form_valid(self, form):
        rendicion_id = self.kwargs.get('rendicion_id')
        rendicion = get_object_or_404(RendicionCometido, pk=rendicion_id)
        form.instance.rendicion = rendicion
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('viaticos:solicitud_detail', kwargs={'pk': self.object.rendicion.solicitud.pk})


class DetalleRendicionGastoUpdateView(StandardUpdateView):
    model = DetalleRendicionGasto
    form_class = DetalleRendicionGastoForm
    template_name = "viaticos/finanzas/detalle_gasto_form.html"
    title = "Editar Comprobante de Gasto Rendido"
    module_name = MODULE_NAME

    def get_success_url(self):
        return reverse('viaticos:solicitud_detail', kwargs={'pk': self.object.rendicion.solicitud.pk})


@login_required
def detalle_rendicion_gasto_delete(request, pk):
    detalle = get_object_or_404(DetalleRendicionGasto, pk=pk)
    solicitud_id = detalle.rendicion.solicitud.pk
    detalle.is_active = False
    detalle.save()
    messages.success(request, 'Comprobante de gasto eliminado de la rendición.')
    return redirect('viaticos:solicitud_detail', pk=solicitud_id)
