from django.urls import reverse_lazy

from core.standard.views import StandardListView, StandardCreateView, StandardUpdateView
from gestion_tic.forms.opcion_campo_tipo_activo import OpcionCampoTipoActivoForm
from gestion_tic.models.opcion_campo_tipo_activo import OpcionCampoTipoActivo

MODULE_NAME = 'Opcion Campo Tipo Activo'


class OpcionCampoTipoActivoListView(StandardListView):
    model = OpcionCampoTipoActivo
    template_name = "gestion_tic/activos/list_opciones_campo_tipo_activo.html"

    title = "Opciones de Campo de Tipo Activo"

    list_url_name = "gestion_tic:opcion_campo_list"
    create_url_name = "gestion_tic:opcion_campo_create"
    update_url_name = "gestion_tic:opcion_campo_update"
    delete_url_name = "gestion_tic:opcion_campo_update"


class OpcionCampoTipoActivoCreateView(StandardCreateView):
    template_name = 'gestion_tic/activos/form_opciones_campo_tipo_activo.html'
    model = OpcionCampoTipoActivo
    form_class = OpcionCampoTipoActivoForm
    success_url = reverse_lazy('gestion_tic:opcion_campo_list')
    title = 'Nueva Opción de Campo'
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.establecimiento = self.request.user.establecimiento
        return super().form_valid(form)


class OpcionCampoTipoActivosUpdateView(StandardUpdateView):
    template_name = 'gestion_tic/activos/form_opciones_campo_tipo_activo.html'
    model = OpcionCampoTipoActivo
    form_class = OpcionCampoTipoActivoForm
    success_url = reverse_lazy('gestion_tic:opcion_campo_list')
    title = 'Editar Opción de Campo'
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
