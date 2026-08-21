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
from ..filters.control_asistencia import FiltroValidacionRelojControl, FiltroPermisoGremial
from ..forms.control_asistencia import ValidacionRelojControlForm, PermisoGremialForm
from ..models.control_asistencia import ValidacionRelojControl, PermisoGremial

MODULE_NAME = 'Control de Asistencia y Reloj'


# ----------------------------------------------------
# 1. Validación Reloj Control
# ----------------------------------------------------

class ValidacionRelojControlListView(StandardListView):
    model = ValidacionRelojControl
    filter_form_class = FiltroValidacionRelojControl
    template_name = "viaticos/control_asistencia/reloj_list.html"
    title = "Cortes de Asistencia y Reloj Control"

    list_url_name = "viaticos:reloj_list"
    create_url_name = "viaticos:reloj_create"
    update_url_name = "viaticos:reloj_update"
    delete_url_name = "viaticos:reloj_delete"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("funcionario", "solicitud")

        if not self.request.user.is_superuser and hasattr(self.request.user, 'establecimiento'):
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)

        if self.filter_form and self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data.get("funcionario"):
                queryset = queryset.filter(funcionario=data["funcionario"])
            if data.get("sincronizado_reloj"):
                queryset = queryset.filter(sincronizado_reloj=(data["sincronizado_reloj"] == '1'))
            if data.get("tipo_ausentismo"):
                queryset = queryset.filter(tipo_ausentismo__icontains=data["tipo_ausentismo"])
            if data.get("fecha_desde"):
                queryset = queryset.filter(fecha_inicio_ausencia__gte=data["fecha_desde"])
            if data.get("fecha_hasta"):
                queryset = queryset.filter(fecha_termino_ausencia__lte=data["fecha_hasta"])

        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class ValidacionRelojControlCreateView(StandardCreateView):
    model = ValidacionRelojControl
    form_class = ValidacionRelojControlForm
    template_name = "viaticos/control_asistencia/reloj_form.html"
    success_url = reverse_lazy("viaticos:reloj_list")
    title = "Nuevo Registro de Corte de Asistencia"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class ValidacionRelojControlUpdateView(StandardUpdateView):
    model = ValidacionRelojControl
    form_class = ValidacionRelojControlForm
    template_name = "viaticos/control_asistencia/reloj_form.html"
    success_url = reverse_lazy("viaticos:reloj_list")
    title = "Editar Corte de Asistencia / Reloj Control"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class ValidacionRelojControlDetailView(StandardDetailView):
    model = ValidacionRelojControl
    title = "Detalle de Corte de Asistencia"
    module_name = MODULE_NAME


@login_required
def validacion_reloj_delete(request, pk):
    corte = get_object_or_404(ValidacionRelojControl, pk=pk)
    corte.is_active = False
    corte.save()
    messages.success(request, 'Registro de corte de asistencia desactivado correctamente.')
    return redirect('viaticos:reloj_list')


@login_required
def sincronizar_reloj_toggle(request, pk):
    corte = get_object_or_404(ValidacionRelojControl, pk=pk)
    corte.sincronizado_reloj = not corte.sincronizado_reloj
    corte.save()
    estado = "sincronizado" if corte.sincronizado_reloj else "desincronizado"
    messages.success(request, f'Registro {estado} con reloj control.')
    return redirect('viaticos:reloj_list')


# ----------------------------------------------------
# 2. Permisos Gremiales
# ----------------------------------------------------

class PermisoGremialListView(StandardListView):
    model = PermisoGremial
    filter_form_class = FiltroPermisoGremial
    template_name = "viaticos/control_asistencia/permiso_gremial_list.html"
    title = "Permisos Gremiales (AFSAG)"

    list_url_name = "viaticos:permiso_gremial_list"
    create_url_name = "viaticos:permiso_gremial_create"
    update_url_name = "viaticos:permiso_gremial_update"
    delete_url_name = "viaticos:permiso_gremial_delete"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("funcionario", "lugar_actividad", "aprobado_por")

        if not self.request.user.is_superuser and hasattr(self.request.user, 'establecimiento'):
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)

        if self.filter_form and self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data.get("folio_gremial"):
                queryset = queryset.filter(folio_gremial=data["folio_gremial"])
            if data.get("ano"):
                queryset = queryset.filter(ano=data["ano"])
            if data.get("funcionario"):
                queryset = queryset.filter(funcionario=data["funcionario"])
            if data.get("aprobado"):
                queryset = queryset.filter(aprobado=(data["aprobado"] == '1'))

        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class PermisoGremialCreateView(StandardCreateView):
    model = PermisoGremial
    form_class = PermisoGremialForm
    template_name = "viaticos/control_asistencia/permiso_gremial_form.html"
    success_url = reverse_lazy("viaticos:permiso_gremial_list")
    title = "Nuevo Permiso Gremial"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class PermisoGremialUpdateView(StandardUpdateView):
    model = PermisoGremial
    form_class = PermisoGremialForm
    template_name = "viaticos/control_asistencia/permiso_gremial_form.html"
    success_url = reverse_lazy("viaticos:permiso_gremial_list")
    title = "Editar Permiso Gremial"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class PermisoGremialDetailView(StandardDetailView):
    model = PermisoGremial
    title = "Detalle de Permiso Gremial"
    module_name = MODULE_NAME


@login_required
def permiso_gremial_delete(request, pk):
    permiso = get_object_or_404(PermisoGremial, pk=pk)
    permiso.is_active = False
    permiso.save()
    messages.success(request, f'Permiso gremial Folio {permiso.folio_gremial}/{permiso.ano} desactivado correctamente.')
    return redirect('viaticos:permiso_gremial_list')
