from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from core.filters.unidad_organizacional import FiltroUnidadOrganizacionalForm
from core.forms.unidad_organizacional import UnidadOrganizacionalForm
from core.models.unidad_organizacional import UnidadOrganizacional


class UnidadOrganizacionalListView(ListView):
    model = UnidadOrganizacional
    template_name = "unidades_organizacionales/list_unidad_organizacional.html"
    context_object_name = "unidades"
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            establecimiento=self.request.user.establecimiento
        ).select_related('establecimiento', 'padre', 'direccion')

        self.filter_form = FiltroUnidadOrganizacionalForm(self.request.GET)

        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data

            if data.get('nombre'):
                # Obtener las unidades que coinciden con el nombre
                matches = queryset.filter(nombre__icontains=data['nombre'])

                # Recolectar IDs de todos los descendientes de las coincidencias
                descendant_ids = set()
                for match in matches:
                    descendant_ids.update(match.get_descendants(include_self=True).values_list('id', flat=True))

                # Reconstruir el queryset con todos los descendientes encontrados
                queryset = self.model.objects.filter(
                    id__in=descendant_ids,
                    establecimiento=self.request.user.establecimiento
                ).select_related('establecimiento', 'padre', 'direccion')

            if data.get('direccion'):
                queryset = queryset.filter(direccion__nombre__icontains=data['direccion'])

            if data.get('es_subdepartamento'):
                queryset = queryset.filter(es_subdepartamento=(data['es_subdepartamento'] == 'True'))

            elif data.get('es_departamento'):
                queryset = queryset.filter(es_departamento=(data['es_departamento'] == 'True'))

            if data.get('is_active'):
                queryset = queryset.filter(is_active=(data['is_active'] == "True"))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        return context


class UnidadOrganizacionalBaseFormView:
    model = UnidadOrganizacional
    form_class = UnidadOrganizacionalForm
    template_name = "unidades_organizacionales/form_unidad_organizacional.html"
    success_url = reverse_lazy("agenda:mantenedores", kwargs={'tipo': 'servicio'})
    page_title = "Formulario Unidad Organizacional"
    submit_label = "Guardar"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["submit_label"] = self.submit_label
        return context


class UnidadOrganizacionalCreateView(UnidadOrganizacionalBaseFormView, CreateView):
    page_title = "Nueva Unidad Organizacional"
    submit_label = "Crear"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Unidad Organizacional creada correctamente.")
        return super().form_valid(form)


class UnidadOrganizacionalUpdateView(UnidadOrganizacionalBaseFormView, UpdateView):
    page_title = "Editar Unidad Organizacional"
    submit_label = "Actualizar"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Unidad Organizacional actualizada correctamente.")
        return super().form_valid(form)
