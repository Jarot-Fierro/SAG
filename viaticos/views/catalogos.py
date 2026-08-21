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
from ..filters.catalogos import FiltroLugarDestino, FiltroEscalaViatico, FiltroVistoLegal
from ..forms.catalogos import LugarDestinoForm, EscalaViaticoForm, VistoLegalForm
from ..models.catalogos import LugarDestino, EscalaViatico, VistoLegal

MODULE_NAME = 'Catálogos de Viáticos'


# ----------------------------------------------------
# 1. Lugares de Destino
# ----------------------------------------------------

class LugarDestinoListView(StandardListView):
    model = LugarDestino
    filter_form_class = FiltroLugarDestino
    template_name = "viaticos/catalogos/lugar_list.html"
    title = "Catálogo de Lugares de Destino"

    list_url_name = "viaticos:lugar_list"
    create_url_name = "viaticos:lugar_create"
    update_url_name = "viaticos:lugar_update"
    delete_url_name = "viaticos:lugar_delete"

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.filter_form and self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data.get("codigo"):
                queryset = queryset.filter(codigo__icontains=data["codigo"])
            if data.get("nombre"):
                queryset = queryset.filter(nombre__icontains=data["nombre"])
            if data.get("region"):
                queryset = queryset.filter(region__icontains=data["region"])
            if data.get("comuna"):
                queryset = queryset.filter(comuna__icontains=data["comuna"])

        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class LugarDestinoCreateView(StandardCreateView):
    model = LugarDestino
    form_class = LugarDestinoForm
    template_name = "viaticos/catalogos/lugar_form.html"
    success_url = reverse_lazy("viaticos:lugar_list")
    title = "Nuevo Lugar de Destino"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class LugarDestinoUpdateView(StandardUpdateView):
    model = LugarDestino
    form_class = LugarDestinoForm
    template_name = "viaticos/catalogos/lugar_form.html"
    success_url = reverse_lazy("viaticos:lugar_list")
    title = "Editar Lugar de Destino"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class LugarDestinoDetailView(StandardDetailView):
    model = LugarDestino
    title = "Detalle de Lugar de Destino"
    module_name = MODULE_NAME


@login_required
def lugar_destino_delete(request, pk):
    filter_kwargs = {'pk': pk}
    if not request.user.is_superuser and hasattr(LugarDestino, 'establecimiento'):
        filter_kwargs['establecimiento'] = request.user.establecimiento

    lugar = get_object_or_404(LugarDestino, **filter_kwargs)
    lugar.is_active = False
    lugar.save()
    messages.success(request, f'Lugar {lugar.nombre} desactivado correctamente.')
    return redirect('viaticos:lugar_list')


# ----------------------------------------------------
# 2. Escala de Viáticos
# ----------------------------------------------------

class EscalaViaticoListView(StandardListView):
    model = EscalaViatico
    filter_form_class = FiltroEscalaViatico
    template_name = "viaticos/catalogos/escala_list.html"
    title = "Escalas Tarifarias de Viáticos"

    list_url_name = "viaticos:escala_list"
    create_url_name = "viaticos:escala_create"
    update_url_name = "viaticos:escala_update"
    delete_url_name = "viaticos:escala_delete"

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.filter_form and self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data.get("ano_vigencia"):
                queryset = queryset.filter(ano_vigencia=data["ano_vigencia"])
            if data.get("grado"):
                queryset = queryset.filter(grado_desde__lte=data["grado"], grado_hasta__gte=data["grado"])
            if data.get("estamento"):
                queryset = queryset.filter(estamento__icontains=data["estamento"])

        return queryset


class EscalaViaticoCreateView(StandardCreateView):
    model = EscalaViatico
    form_class = EscalaViaticoForm
    template_name = "viaticos/catalogos/escala_form.html"
    success_url = reverse_lazy("viaticos:escala_list")
    title = "Nueva Escala de Viático"
    module_name = MODULE_NAME


class EscalaViaticoUpdateView(StandardUpdateView):
    model = EscalaViatico
    form_class = EscalaViaticoForm
    template_name = "viaticos/catalogos/escala_form.html"
    success_url = reverse_lazy("viaticos:escala_list")
    title = "Editar Escala de Viático"
    module_name = MODULE_NAME


class EscalaViaticoDetailView(StandardDetailView):
    model = EscalaViatico
    title = "Detalle de Escala de Viático"
    module_name = MODULE_NAME


@login_required
def escala_viatico_delete(request, pk):
    escala = get_object_or_404(EscalaViatico, pk=pk)
    escala.is_active = False
    escala.save()
    messages.success(request, 'Escala de viático desactivada correctamente.')
    return redirect('viaticos:escala_list')


# ----------------------------------------------------
# 3. Vistos Legales
# ----------------------------------------------------

class VistoLegalListView(StandardListView):
    model = VistoLegal
    filter_form_class = FiltroVistoLegal
    template_name = "viaticos/catalogos/visto_list.html"
    title = "Catálogo de Vistos Legales"

    list_url_name = "viaticos:visto_list"
    create_url_name = "viaticos:visto_create"
    update_url_name = "viaticos:visto_update"
    delete_url_name = "viaticos:visto_delete"

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.filter_form and self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data.get("codigo"):
                queryset = queryset.filter(codigo__icontains=data["codigo"])
            if data.get("corresponde_a"):
                queryset = queryset.filter(corresponde_a__icontains=data["corresponde_a"])
            if data.get("q"):
                queryset = queryset.filter(texto_visto__icontains=data["q"])

        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class VistoLegalCreateView(StandardCreateView):
    model = VistoLegal
    form_class = VistoLegalForm
    template_name = "viaticos/catalogos/visto_form.html"
    success_url = reverse_lazy("viaticos:visto_list")
    title = "Nuevo Visto Legal"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class VistoLegalUpdateView(StandardUpdateView):
    model = VistoLegal
    form_class = VistoLegalForm
    template_name = "viaticos/catalogos/visto_form.html"
    success_url = reverse_lazy("viaticos:visto_list")
    title = "Editar Visto Legal"
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class VistoLegalDetailView(StandardDetailView):
    model = VistoLegal
    title = "Detalle de Visto Legal"
    module_name = MODULE_NAME


@login_required
def visto_legal_delete(request, pk):
    filter_kwargs = {'pk': pk}
    if not request.user.is_superuser and hasattr(VistoLegal, 'establecimiento'):
        filter_kwargs['establecimiento'] = request.user.establecimiento

    visto = get_object_or_404(VistoLegal, **filter_kwargs)
    visto.is_active = False
    visto.save()
    messages.success(request, f'Visto legal {visto.codigo} desactivado correctamente.')
    return redirect('viaticos:visto_list')
