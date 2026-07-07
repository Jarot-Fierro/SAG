from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView

from core.utils import IncludeUserFormCreate, IncludeUserFormUpdate
from ..forms.computador import FormComputador
from ..models.equipos import Equipo, AsignacionIP


class EquipoBaseView(LoginRequiredMixin):
    template_name = 'gestion_tic/equipos/form.html'
    success_url = None
    module_name = 'Catálogo'
    title = 'Mantenedor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module_name'] = self.module_name
        context['title'] = self.title
        context['list_url'] = self.get_list_url()
        context['create_url'] = self.get_create_url()
        return context

    def get_list_url(self):
        return None

    def get_create_url(self):
        return None


class EquipoListView(EquipoBaseView, ListView):
    template_name = 'gestion_tic/equipos/list.html'
    context_object_name = 'objetos'
    paginate_by = 10
    search_fields = ['nombre']

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        query = self.request.GET.get('q')
        if query and self.search_fields:
            search_query = Q()
            for field in self.search_fields:
                search_query |= Q(**{f"{field}__icontains": query})
            queryset = queryset.filter(search_query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['update_url_name'] = self.update_url_name
        context['delete_url_name'] = self.delete_url_name
        context['q'] = self.request.GET.get('q', '')
        return context


class EquipoCreateView(EquipoBaseView, IncludeUserFormCreate, CreateView):
    def form_valid(self, form):
        messages.success(self.request, f'{self.model._meta.verbose_name} creado correctamente.')
        return super().form_valid(form)


class EquipoUpdateView(EquipoBaseView, IncludeUserFormUpdate, UpdateView):
    def form_valid(self, form):
        messages.success(self.request, f'{self.model._meta.verbose_name} actualizado correctamente.')
        return super().form_valid(form)


def equipos_desactivar(request, pk, model, redirect_url_name):
    obj = get_object_or_404(model, pk=pk)
    obj.is_active = False
    obj.save()
    messages.success(request, f'{obj} desactivado correctamente.')
    return redirect(redirect_url_name)


class ComputadorListView(EquipoListView):
    model = Equipo
    title = 'Listado de Computadores'
    update_url_name = 'gestion_tic:computador_update'
    delete_url_name = 'gestion_tic:computador_delete'
    search_fields = [
        'serie', 'mac', 'ip__ip', 'responsable__first_name',
        'responsable__last_name', 'marca__nombre', 'modelo__nombre'
    ]

    def get_queryset(self):
        # Filtramos por tipo PC y optimizamos consultas
        return super().get_queryset().filter(tipo_equipo='PC').select_related(
            'marca', 'modelo', 'tipo_pc', 'sistema_operativo',
            'responsable', 'propietario', 'jefe_entrega', 'contrato', 'ip', 'departamento'
        )

    def get_create_url(self):
        return reverse_lazy('gestion_tic:computador_create')


class ComputadorCreateView(EquipoCreateView):
    model = Equipo
    form_class = FormComputador
    title = 'Nuevo Computador'
    success_url = reverse_lazy('gestion_tic:computador_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:computador_list')

    def form_valid(self, form):
        computador = form.save(commit=False)
        computador.tipo_equipo = 'PC'
        # Asignar establecimiento del usuario si está disponible
        if hasattr(self.request.user, 'establecimiento'):
            computador.establecimiento = self.request.user.establecimiento

        computador.save()

        # Lógica de Asignación de IP
        if computador.ip:
            AsignacionIP.objects.filter(ip=computador.ip).exclude(equipo=computador).delete()
            AsignacionIP.objects.update_or_create(
                equipo=computador,
                defaults={'ip': computador.ip, 'activa': True}
            )
        else:
            AsignacionIP.objects.filter(equipo=computador).delete()

        messages.success(self.request, f'{self.model._meta.verbose_name} creado correctamente.')
        return redirect(self.success_url)


class ComputadorUpdateView(EquipoUpdateView):
    model = Equipo
    form_class = FormComputador
    title = 'Editar Computador'
    success_url = reverse_lazy('gestion_tic:computador_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:computador_list')

    def form_valid(self, form):
        # Obtenemos el objeto antes de guardar para comparar IPs
        old_instance = self.get_object()
        old_ip = old_instance.ip

        computador = form.save()
        new_ip = computador.ip

        if old_ip and old_ip != new_ip:
            AsignacionIP.objects.filter(equipo=computador, ip=old_ip).delete()

        if new_ip:
            AsignacionIP.objects.filter(ip=new_ip).exclude(equipo=computador).delete()
            AsignacionIP.objects.update_or_create(
                equipo=computador,
                defaults={'ip': new_ip, 'activa': True}
            )
        else:
            AsignacionIP.objects.filter(equipo=computador).delete()

        messages.success(self.request, f'{self.model._meta.verbose_name} actualizado correctamente.')
        return redirect(self.success_url)


def computador_desactivar(request, pk):
    return equipos_desactivar(request, pk, Equipo, 'gestion_tic:computador_list')
