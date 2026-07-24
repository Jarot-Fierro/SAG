from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView

from gestion_tic.filters.computador import ComputadorFilter
from gestion_tic.forms.computador import FormComputador
from gestion_tic.models.equipos import Equipo


class ComputadorListView(LoginRequiredMixin, ListView):
    model = Equipo
    template_name = "gestion_tic/equipos/list_computador.html"
    context_object_name = "objetos"
    paginate_by = 10

    def get_queryset(self):
        # Filtrar por tipo PC, establecimiento del usuario y que esté activo
        queryset = self.model.objects.filter(
            tipo_equipo='PC',
            establecimiento=self.request.user.establecimiento,
            is_active=True
        ).select_related(
            'marca', 'modelo', 'tipo_pc', 'ip', 'responsable', 'propietario'
        )

        self.filter_form = ComputadorFilter(self.request.GET)

        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data

            if data.get("tipo_pc"):
                queryset = queryset.filter(tipo_pc=data["tipo_pc"])

            if data.get("marca"):
                queryset = queryset.filter(marca=data["marca"])

            if data.get("serie"):
                queryset = queryset.filter(serie__icontains=data["serie"])

            if data.get("ip"):
                queryset = queryset.filter(ip__ip__icontains=data["ip"])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        context["title"] = "Listado de Computadores"
        context["create_url"] = reverse_lazy('gestion_tic:computador_create')
        context["update_url_name"] = 'gestion_tic:computador_update'
        context["delete_url_name"] = 'gestion_tic:computador_delete'
        return context


class ComputadorCreateView(LoginRequiredMixin, CreateView):
    model = Equipo
    form_class = FormComputador
    template_name = "gestion_tic/equipos/form_computador.html"
    success_url = reverse_lazy('gestion_tic:computador_list')

    def form_valid(self, form):
        form.instance.establecimiento = self.request.user.establecimiento
        form.instance.tipo_equipo = 'PC'
        messages.success(self.request, "Computador creado exitosamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Nuevo Computador"
        context["list_url"] = reverse_lazy('gestion_tic:computador_list')
        return context


class ComputadorUpdateView(LoginRequiredMixin, UpdateView):
    model = Equipo
    form_class = FormComputador
    template_name = "gestion_tic/equipos/form.html"
    success_url = reverse_lazy('gestion_tic:computador_list')

    def get_queryset(self):
        return self.model.objects.filter(
            establecimiento=self.request.user.establecimiento,
            tipo_equipo='PC'
        )

    def form_valid(self, form):
        messages.success(self.request, "Computador actualizado exitosamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Editar Computador: {self.object.serie}"
        context["list_url"] = reverse_lazy('gestion_tic:computador_list')
        return context


def computador_desactivar(request, pk):
    objeto = get_object_or_404(
        Equipo,
        pk=pk,
        establecimiento=request.user.establecimiento,
        tipo_equipo='PC'
    )
    objeto.is_active = False
    objeto.save()
    messages.success(request, "Computador desactivado exitosamente.")
    return redirect('gestion_tic:computador_list')
