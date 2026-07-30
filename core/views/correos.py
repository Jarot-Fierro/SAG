from core.forms.configuracion_correo import ConfiguracionCorreoForm
from core.models.configuracion_correo import ConfiguracionCorreo
from core.standard.views import *


class CorreoListView(StandardListView):
    model = ConfiguracionCorreo
    title = 'Listado de Configuraciones de Correo'
    list_url_name = 'core:correo_list'
    create_url_name = 'core:correo_create'
    update_url_name = 'core:correo_update'
    delete_url_name = 'core:correo_delete'
    search_fields = ['establecimiento__nombre', 'email_remitente']


class CorreoCreateView(StandardCreateView):
    model = ConfiguracionCorreo
    form_class = ConfiguracionCorreoForm
    title = 'Crear Configuración de Correo'
    success_url = reverse_lazy('core:correo_list')

    def dispatch(self, request, *args, **kwargs):
        # Si ya existe una configuración para el establecimiento del usuario, redirigir al listado o edición
        if ConfiguracionCorreo.objects.filter(establecimiento=request.user.establecimiento).exists():
            messages.warning(request, 'Ya existe una configuración de correo para su establecimiento.')
            return redirect('core:correo_list')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_list_url(self):
        return reverse_lazy('core:correo_list')

    def form_valid(self, form):
        form.instance.establecimiento = self.request.user.establecimiento

        return super().form_valid(form)


class CorreoUpdateView(StandardUpdateView):
    model = ConfiguracionCorreo
    form_class = ConfiguracionCorreoForm
    title = 'Editar Configuración de Correo'
    success_url = reverse_lazy('core:correo_list')

    def get_list_url(self):
        return reverse_lazy('core:correo_list')


@require_POST
def correo_desactivar(request, pk):
    return catalogo_desactivar(request, pk, ConfiguracionCorreo, 'core:correo_list')
