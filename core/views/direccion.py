from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from core.forms.direccion import DireccionForm
from core.models.direccion import Direccion


class DireccionListView(ListView):
    model = Direccion
    template_name = "direcciones/list_direccion.html"
    context_object_name = "direcciones"
    paginate_by = 25

    def get_queryset(self):
        return super().get_queryset().filter(establecimiento=self.request.user.establecimiento)


class DireccionBaseFormView:
    model = Direccion
    form_class = DireccionForm
    template_name = "direcciones/form_direccion.html"
    success_url = reverse_lazy("agenda:mantenedores", kwargs={'tipo': 'direccion'})
    page_title = "Formulario Dirección"
    submit_label = "Guardar"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["submit_label"] = self.submit_label
        return context


class DireccionCreateView(DireccionBaseFormView, CreateView):
    page_title = "Nueva Dirección"
    submit_label = "Crear"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Dirección creada correctamente.")
        return super().form_valid(form)


class DireccionUpdateView(DireccionBaseFormView, UpdateView):
    page_title = "Editar Dirección"
    submit_label = "Actualizar"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Dirección actualizada correctamente.")
        return super().form_valid(form)
