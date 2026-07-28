from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView


class StandardBaseView(LoginRequiredMixin):
    template_name = 'mantenedores/form.html'
    success_url = None
    module_name = 'Mantenedor'
    title = 'Mantenedor'

    def get_queryset(self):
        queryset = self.model.objects.all()
        # Si el modelo tiene el campo 'establecimiento', filtramos por él
        if hasattr(self.model, 'establecimiento'):
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)

        # Si el modelo tiene 'is_active', filtramos por él
        if hasattr(self.model, 'is_active'):
            queryset = queryset.filter(is_active=True)
        elif hasattr(self.model, 'activo'):
            queryset = queryset.filter(activo=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['list_url'] = self.get_list_url()
        context['create_url'] = self.get_create_url()
        return context

    def get_list_url(self):
        url_name = getattr(self, 'list_url_name', None)
        if url_name:
            return reverse_lazy(url_name)
        return ''

    def get_create_url(self):
        url_name = getattr(self, 'create_url_name', None)
        if url_name:
            return reverse_lazy(url_name)
        return ''


class StandardListView(StandardBaseView, ListView):
    template_name = 'mantenedores/list.html'
    context_object_name = 'objetos'
    paginate_by = 10
    search_fields = ['nombre']

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
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


class StandardCreateView(StandardBaseView, CreateView):
    def form_valid(self, form):
        if hasattr(form.instance, 'establecimiento'):
            form.instance.establecimiento = self.request.user.establecimiento

        if hasattr(form.instance, 'created_by'):
            form.instance.created_by = self.request.user

        messages.success(self.request, f'{self.model._meta.verbose_name} creado correctamente.')
        return super().form_valid(form)


class StandardUpdateView(StandardBaseView, UpdateView):
    def form_valid(self, form):
        if hasattr(form.instance, 'updated_by'):
            form.instance.updated_by = self.request.user

        messages.success(self.request, f'{self.model._meta.verbose_name} actualizado correctamente.')
        return super().form_valid(form)


@require_POST
def catalogo_desactivar(request, pk, model, redirect_url_name):
    # Intentamos filtrar por establecimiento si el modelo lo tiene
    filter_kwargs = {'pk': pk}
    if hasattr(model, 'establecimiento'):
        filter_kwargs['establecimiento'] = request.user.establecimiento

    obj = get_object_or_404(model, **filter_kwargs)

    if hasattr(obj, 'is_active'):
        obj.is_active = False
    elif hasattr(obj, 'activo'):
        obj.activo = False

    obj.save()
    messages.success(request, f'{obj} desactivado correctamente.')
    return redirect(redirect_url_name)
