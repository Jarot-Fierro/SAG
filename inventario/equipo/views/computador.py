from core.history import GenericHistoryListView
from core.mixin import DataTableMixin
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import CreateView, UpdateView, DetailView

from core.utils import IncludeUserFormCreate, IncludeUserFormUpdate
from equipo.forms.computador import FormComputador
from equipo.models.equipos import Equipo

MODULE_NAME = 'Computadores'

from django.urls import reverse_lazy
from django.views.generic import TemplateView


class ComputadorListView(LoginRequiredMixin, DataTableMixin, TemplateView):
    template_name = 'computador/list.html'
    model = Equipo

    datatable_columns = [
        'ID',
        'Serial',
        'Tipo Equipo',
        'Marca',
        'Modelo',
        'MAC',
        'IP',
        'Responsable',
        'Sistema Operativo',
        'Propietario',
        'Contrato',
        'Jefe Entrega',
    ]

    datatable_order_fields = [
        'id',
        'serie',
        'tipo__nombre',
        'marca__nombre',
        'modelo__nombre',
        'mac',
        'ip__ip',
        'responsable__first_name',
        'sistema_operativo__nombre',
        'propietario__nombre',
        'contrato__numero',
        'jefe_tic__nombre',
    ]

    datatable_search_fields = [
        'serie__icontains',
        'tipo__nombre__icontains',
        'marca__nombre__icontains',
        'modelo__nombre__icontains',
        'mac__icontains',
        'ip__ip__icontains',
        'responsable__first_name__icontains',
        'responsable__last_name__icontains',
        'sistema_operativo__nombre__icontains',
        'propietario__nombre__icontains',
        'contrato__numero__icontains',
        'jefe_tic__nombre__icontains',
    ]

    # url_update = 'update_computador'

    def get_url_update(self):
        user = self.request.user
        if getattr(user, 'rol', None) and user.rol.equipos == 2:
            return 'update_computador'
        return None

    def render_row(self, obj):
        return {
            'ID': obj.id,
            'Serial': obj.serie if obj.serie else '-',
            'Tipo Equipo': obj.tipo_pc.nombre.upper() if obj.tipo_pc else '-',
            'Marca': obj.marca.nombre.upper() if obj.marca else '-',
            'Modelo': obj.modelo.nombre.upper() if obj.modelo else '-',
            'MAC': obj.mac if obj.mac else '-',
            # 'IP': obj.ip.ip if obj.ip else '-',
            'IP': (
                f'<span class="badge bg-success p-2">{obj.ip.ip}</span>'
                if obj.ip
                else '-'
            ),
            'Responsable': (
                f'<span class="badge rounded-pill bg-primary p-2">{obj.responsable.nombres.upper()}</span>'
                if obj.responsable
                else '<span class="badge rounded-pill bg-secondary">SIN RESPONSABLE</span>'
            ),
            'Sistema Operativo': obj.sistema_operativo.nombre.upper() if obj.sistema_operativo else '-',
            'Propietario': obj.propietario.nombre.upper() if obj.propietario else '-',
            'Contrato': obj.contrato.nombre if obj.contrato else '-',
            'Jefe Entrega': obj.jefe_entrega.nombre.upper() if obj.jefe_entrega else '-',
        }

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('datatable'):
            return self.get_datatable_response(request)
        return super().get(request, *args, **kwargs)

    def get_base_queryset(self):
        # 🔥 Optimización importante y filtro por tipo PC
        return Equipo.objects.filter(tipo_equipo='PC').select_related(
            'marca',
            'modelo',
            'tipo_pc',
            'sistema_operativo',
            'microsoft_office',
            'responsable',
            'propietario',
            'jefe_entrega',
            'contrato',
            'ip'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Listado de Computadores',
            'list_url': reverse_lazy('list_computador'),
            'create_url': reverse_lazy('create_computador'),
            'datatable_enabled': True,
            'datatable_order': [[0, 'asc']],
            'datatable_page_length': 100,
            'columns': self.datatable_columns,
        })
        return context

    def get_actions(self, obj):
        """
        Agrega botones personalizados a la columna de acciones.
        """
        actions = super().get_actions(obj)
        # Botón para generar acta PDF del Computador
        if obj.responsable:

            pdf_button = f"""
                <a href="{reverse_lazy('acta_computador', kwargs={'pk': obj.id})}"
                   target="_blank"
                   class="btn p-1 btn-sm btn-danger" title="Ver Acta PDF">
                   <i class="fas fa-file-pdf"></i></a>
            """
            return actions + pdf_button
        else:
            return actions
        # return actions


class ComputadorDetailView(LoginRequiredMixin, DetailView):
    model = Equipo
    template_name = 'computador/detail.html'

    def render_to_response(self, context, **response_kwargs):
        # Si es una solicitud AJAX, devolvemos solo el fragmento HTML
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.template.loader import render_to_string
            html = render_to_string(self.template_name, context=context, request=self.request)
            return HttpResponse(html)
        return super().render_to_response(context, **response_kwargs)


class ComputadorCreateView(LoginRequiredMixin, IncludeUserFormCreate, CreateView):
    template_name = 'computador/form.html'
    model = Equipo
    form_class = FormComputador
    success_url = reverse_lazy('list_computador')

    def form_valid(self, form):
        computador = form.save(commit=False)

        # Asignación automática del tipo de equipo
        computador.tipo_equipo = 'PC'

        # asignar establecimiento del usuario
        computador.establecimiento = self.request.user.establecimiento

        computador.save()

        # Marcar la IP como asignada si se proporcionó una
        if computador.ip:
            # Crear o actualizar registro en AsignacionIP
            from equipo.models.equipos import AsignacionIP
            # Eliminar si la IP ya estaba asignada a otro equipo
            AsignacionIP.objects.filter(ip=computador.ip).exclude(equipo=computador).delete()

            AsignacionIP.objects.update_or_create(
                equipo=computador,
                defaults={
                    'ip': computador.ip,
                    'activa': True
                }
            )
        else:
            # Si se crea sin IP, aseguramos que no haya registro (aunque es poco probable en creación)
            from equipo.models.equipos import AsignacionIP
            AsignacionIP.objects.filter(equipo=computador).delete()

        messages.success(self.request, 'Computador creado correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Computador'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        context['module_name'] = MODULE_NAME
        return context


class ComputadorUpdateView(LoginRequiredMixin, IncludeUserFormUpdate, UpdateView):
    template_name = 'computador/form.html'
    model = Equipo
    form_class = FormComputador
    success_url = reverse_lazy('list_computador')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Obtenemos el objeto anterior para saber si cambió la IP
        old_equipo = self.get_object()
        old_ip = old_equipo.ip

        computador = form.save()
        new_ip = computador.ip

        from equipo.models.equipos import AsignacionIP

        # Si la IP cambió o fue removida
        if old_ip and old_ip != new_ip:
            # Eliminar asignación previa
            AsignacionIP.objects.filter(equipo=computador, ip=old_ip).delete()

        # Si se asignó una nueva IP o se mantiene la misma
        if new_ip:
            # Buscar si ya existe una asignación para este equipo
            # y si existe una para la IP en otro equipo, borrarla para evitar error de unicidad
            AsignacionIP.objects.filter(ip=new_ip).exclude(equipo=computador).delete()

            AsignacionIP.objects.update_or_create(
                equipo=computador,
                defaults={
                    'ip': new_ip,
                    'activa': True
                }
            )
        else:
            # Si el equipo ya no tiene IP, eliminamos cualquier asignación que tuviera
            AsignacionIP.objects.filter(equipo=computador).delete()

        messages.success(self.request, 'Computador actualizada correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Computador'
        context['list_url'] = self.success_url
        context['action'] = 'edit'
        context['module_name'] = MODULE_NAME
        return context


class ComputadorArmadoCreateView(ComputadorCreateView):
    def form_valid(self, form):
        computador = form.save(commit=False)
        computador.es_armado = True
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Computador Armado'
        context['is_armado'] = True
        return context


class ComputadorHistoryListView(LoginRequiredMixin, GenericHistoryListView):
    base_model = Equipo
    template_name = 'history/list.html'
