from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy

from core.standard.views import (
    StandardListView,
    StandardCreateView,
    StandardUpdateView,
    StandardDetailView,
)
from ..filters.transporte import FiltroGastoTransporte
from ..forms.transporte import GastoTransporteForm
from ..models.transporte import GastoTransporte

MODULE_NAME = 'Transporte y Pasajes'


class GastoTransporteListView(StandardListView):
    model = GastoTransporte
    filter_form_class = FiltroGastoTransporte
    template_name = "viaticos/transporte/transporte_list.html"
    title = "Gestión de Transporte, Pasajes y Vales"

    list_url_name = "viaticos:transporte_list"
    create_url_name = "viaticos:transporte_create"
    update_url_name = "viaticos:transporte_update"
    delete_url_name = "viaticos:transporte_delete"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("solicitud", "solicitud__funcionario")

        if not self.request.user.is_superuser:
            queryset = queryset.filter(solicitud__establecimiento=self.request.user.establecimiento)

        if self.filter_form and self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data.get("tipo_gasto"):
                queryset = queryset.filter(tipo_gasto=data["tipo_gasto"])
            if data.get("origen"):
                queryset = queryset.filter(origen__icontains=data["origen"])
            if data.get("destino"):
                queryset = queryset.filter(destino__icontains=data["destino"])
            if data.get("fecha_desde"):
                queryset = queryset.filter(fecha_ida__gte=data["fecha_desde"])
            if data.get("fecha_hasta"):
                queryset = queryset.filter(fecha_ida__lte=data["fecha_hasta"])

        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class GastoTransporteCreateView(StandardCreateView):
    model = GastoTransporte
    form_class = GastoTransporteForm
    template_name = "viaticos/transporte/transporte_form.html"
    success_url = reverse_lazy("viaticos:transporte_list")
    title = "Nuevo Registro de Transporte / Pasaje"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class GastoTransporteUpdateView(StandardUpdateView):
    model = GastoTransporte
    form_class = GastoTransporteForm
    template_name = "viaticos/transporte/transporte_form.html"
    success_url = reverse_lazy("viaticos:transporte_list")
    title = "Editar Registro de Transporte / Pasaje"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class GastoTransporteDetailView(StandardDetailView):
    model = GastoTransporte
    title = "Detalle de Gasto de Transporte"
    module_name = MODULE_NAME


@login_required
def gasto_transporte_delete(request, pk):
    gasto = get_object_or_404(GastoTransporte, pk=pk)
    gasto.is_active = False
    gasto.save()
    messages.success(request, 'Registro de transporte desactivado correctamente.')
    return redirect('viaticos:transporte_list')
