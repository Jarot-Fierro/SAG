from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from core.standard.views import (
    StandardListView,
    StandardCreateView,
    StandardUpdateView,
    StandardDetailView,
)
from ..filters.resoluciones import FiltroResolucionCometido
from ..forms.resoluciones import ResolucionCometidoForm
from ..models.resoluciones import ResolucionCometido
from ..models.solicitud import SolicitudCometidoViatico

MODULE_NAME = 'Resoluciones Exentas de Cometidos'


class ResolucionCometidoListView(StandardListView):
    model = ResolucionCometido
    filter_form_class = FiltroResolucionCometido
    template_name = "viaticos/resoluciones/resolucion_list.html"
    title = "Resoluciones Exentas de Cometidos y Viáticos"

    list_url_name = "viaticos:resolucion_list"
    create_url_name = "viaticos:resolucion_create"
    update_url_name = "viaticos:resolucion_update"
    delete_url_name = "viaticos:resolucion_delete"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("solicitud", "solicitud__funcionario")

        if not self.request.user.is_superuser and hasattr(self.request.user, 'establecimiento'):
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)

        if self.filter_form and self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data.get("numero_resolucion"):
                queryset = queryset.filter(numero_resolucion=data["numero_resolucion"])
            if data.get("ano_resolucion"):
                queryset = queryset.filter(ano_resolucion=data["ano_resolucion"])
            if data.get("firmante"):
                queryset = queryset.filter(firmante_nombre__icontains=data["firmante"])
            if data.get("fecha_desde"):
                queryset = queryset.filter(fecha_emision__gte=data["fecha_desde"])
            if data.get("fecha_hasta"):
                queryset = queryset.filter(fecha_emision__lte=data["fecha_hasta"])

        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class ResolucionCometidoCreateView(StandardCreateView):
    model = ResolucionCometido
    form_class = ResolucionCometidoForm
    template_name = "viaticos/resoluciones/resolucion_form.html"
    title = "Emitir Nueva Resolución Exenta"
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
                initial[
                    'considerandos'] = f"Visto el cometido funcional folio {solicitud.folio}/{solicitud.ano} del funcionario {solicitud.funcionario} para realizar labores de {solicitud.motivo_viaje[:100]}."
                initial[
                    'texto_resuelve'] = f"1° AUTORÍZASE la comisión de servicio del funcionario {solicitud.funcionario} desde el {solicitud.fecha_inicio.strftime('%d/%m/%Y')} al {solicitud.fecha_termino.strftime('%d/%m/%Y')}."
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        # Actualizar estado de solicitud
        self.object.solicitud.estado = 'RESOLUCION_EMITIDA'
        self.object.solicitud.save()
        return response

    def get_success_url(self):
        return reverse('viaticos:solicitud_detail', kwargs={'pk': self.object.solicitud.pk})


class ResolucionCometidoUpdateView(StandardUpdateView):
    model = ResolucionCometido
    form_class = ResolucionCometidoForm
    template_name = "viaticos/resoluciones/resolucion_form.html"
    title = "Editar Resolución Exenta"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        return reverse('viaticos:solicitud_detail', kwargs={'pk': self.object.solicitud.pk})


class ResolucionCometidoDetailView(StandardDetailView):
    model = ResolucionCometido
    title = "Detalle de Resolución Exenta"
    module_name = MODULE_NAME


@login_required
def resolucion_cometido_delete(request, pk):
    resolucion = get_object_or_404(ResolucionCometido, pk=pk)
    resolucion.is_active = False
    resolucion.save()
    messages.success(request,
                     f'Resolución N° {resolucion.numero_resolucion}/{resolucion.ano_resolucion} desactivada correctamente.')
    return redirect('viaticos:resolucion_list')
