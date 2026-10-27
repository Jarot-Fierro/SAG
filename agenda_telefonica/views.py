from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from weasyprint import HTML

from agenda_telefonica.decorators import user_editor_module
from agenda_telefonica.forms import FormAnexos
from agenda_telefonica.models import Anexo
from agenda_telefonica.models import PerfilAgenda
from core.models import Establecimiento
from core.models.unidad_organizacional import UnidadOrganizacional
from core.standard.views import StandardCreateView, StandardUpdateView


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class IndexView(TemplateView):
    template_name = 'anexos/index.html'

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse(
                {'error': 'Acción no válida'},
                status=400
            )

        draw = int(request.POST.get('draw', 1))
        start = max(0, int(request.POST.get('start', 0)))
        length = int(request.POST.get('length', 25))

        establecimiento_id = _as_int(request.GET.get('establecimiento'), 1)

        if not Establecimiento.objects.filter(pk=establecimiento_id).exists():
            establecimiento_id = 1

        queryset = Anexo.objects.filter(
            establecimiento_id=establecimiento_id,
            is_active=True
        )

        # Total sin filtros
        records_total = queryset.count()

        # Búsqueda global
        search = request.POST.get('search[value]', '')

        if search:
            queryset = queryset.filter(
                Q(anexo__icontains=search) |
                Q(numero_telefonico__icontains=search) |
                Q(nombre_anexo__icontains=search) |
                Q(email__icontains=search) |
                Q(unidad_organizacional__nombre__icontains=search) |
                Q(unidad_organizacional__direccion__nombre__icontains=search) |
                Q(encargado_de__icontains=search)
            )

        prefijo = 'columns[5][columnControl][list]'
        departamentos = []

        for key, values in request.POST.lists():
            if key == prefijo or key.startswith(prefijo + '['):
                departamentos.extend(values)

        if departamentos:
            unidades_seleccionadas = UnidadOrganizacional.objects.filter(
                establecimiento_id=establecimiento_id,
                nombre__in=departamentos,
            )

            unidades_incluidas = (
                UnidadOrganizacional.objects.get_queryset_descendants(
                    unidades_seleccionadas,
                    include_self=True,
                )
                .filter(establecimiento_id=establecimiento_id)
            )

            queryset = queryset.filter(
                unidad_organizacional__in=unidades_incluidas,
            )

        # Ordenamiento: mismo orden de columnas que en index.js
        columnas = {
            0: 'anexo',
            1: 'anexo_publico',
            2: 'numero_telefonico',
            3: 'nombre_anexo',
            4: 'email',
            5: 'unidad_organizacional__nombre',
            6: 'unidad_organizacional__direccion__nombre',
            7: 'encargado_de',
        }

        order_index = _as_int(request.POST.get('order[0][column]'), 0)
        order_dir = request.POST.get('order[0][dir]', 'asc')

        campo = columnas.get(order_index, 'anexo')

        if order_dir == 'desc':
            campo = f'-{campo}'

        queryset = queryset.order_by(campo, 'pk')

        # Total después de filtrar
        records_filtered = queryset.count()

        # Paginación
        if length != -1:
            queryset = queryset[start:start + length]

        # print(queryset.query)

        data = list(queryset.values(
            'anexo',
            'anexo_publico',
            'numero_telefonico',
            'nombre_anexo',
            'email',
            'unidad_organizacional__nombre',
            'unidad_organizacional__direccion__nombre',
            'unidad_organizacional__direccion__enlace_google_maps',
            'encargado_de',
        ))

        opciones_departamentos = [
            {
                'label': departamento.nombre,
                'value': departamento.nombre
            }
            for departamento in
            UnidadOrganizacional.objects.filter(
                Q(es_departamento=True) | Q(es_subdepartamento=True) | Q(unidad_principal=True),
                establecimiento_id=establecimiento_id,
            ).order_by('nombre')
        ]

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
            'columnControl': {
                'unidad_organizacional__nombre': opciones_departamentos
            }
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        establecimiento_id = _as_int(
            self.request.GET.get('establecimiento'), 1
        )

        establecimiento = Establecimiento.objects.filter(
            pk=establecimiento_id
        ).first()

        if establecimiento is None:
            establecimiento = get_object_or_404(Establecimiento, pk=1)

        context['establecimiento'] = establecimiento
        return context


@method_decorator(user_editor_module, name='dispatch')
class ListEditAnexosView(TemplateView):
    template_name = 'anexos/list_edit_anexos.html'

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse(
                {'error': 'Acción no válida'},
                status=400
            )

        draw = int(request.POST.get('draw', 1))
        start = max(0, int(request.POST.get('start', 0)))
        length = int(request.POST.get('length', 10))

        if request.user.is_authenticated and request.user.establecimiento:
            establecimiento_id = request.user.establecimiento.id
        else:
            establecimiento_id = _as_int(request.GET.get('establecimiento'), 1)
            if not Establecimiento.objects.filter(pk=establecimiento_id).exists():
                establecimiento_id = 1

        queryset = Anexo.objects.filter(
            establecimiento_id=establecimiento_id,
            is_active=True
        )

        unidades_permitidas_ids = set()
        if request.user.is_authenticated and hasattr(request.user, 'perfilagenda'):
            perfil = request.user.perfilagenda
            unidades_permitidas = perfil.unidad_organizacional.all()
            if unidades_permitidas.exists():
                for unidad in unidades_permitidas:
                    for desc in unidad.get_descendants(include_self=True):
                        unidades_permitidas_ids.add(desc.id)

                queryset = queryset.filter(
                    Q(unidad_organizacional_id__in=unidades_permitidas_ids) |
                    Q(funcionario__unidad_organizacional_id__in=unidades_permitidas_ids)
                )

        # Total sin filtros adicionales de búsqueda
        records_total = queryset.count()

        # Búsqueda global
        search = request.POST.get('search[value]', '')

        if search:
            queryset = queryset.filter(
                Q(anexo__icontains=search) |
                Q(numero_telefonico__icontains=search) |
                Q(nombre_anexo__icontains=search) |
                Q(email__icontains=search) |
                Q(unidad_organizacional__nombre__icontains=search) |
                Q(funcionario__unidad_organizacional__nombre__icontains=search) |
                Q(unidad_organizacional__direccion__nombre__icontains=search) |
                Q(funcionario__unidad_organizacional__direccion__nombre__icontains=search) |
                Q(encargado_de__icontains=search) |
                Q(funcionario__cargo__icontains=search) |
                Q(funcionario__nombres__icontains=search) |
                Q(funcionario__apellidos__icontains=search)
            )

        prefijo = 'columns[5][columnControl][list]'
        departamentos = []

        for key, values in request.POST.lists():
            if key == prefijo or key.startswith(prefijo + '['):
                departamentos.extend(values)

        if departamentos:
            queryset = queryset.filter(
                Q(unidad_organizacional__nombre__in=departamentos) |
                Q(funcionario__unidad_organizacional__nombre__in=departamentos),
                establecimiento_id=establecimiento_id
            )

        # Ordenamiento
        columnas = {
            0: 'anexo',
            1: 'anexo_publico',
            2: 'numero_telefonico',
            3: 'nombre_anexo',
            4: 'email',
            5: 'unidad_organizacional__nombre',
            6: 'unidad_organizacional__direccion__nombre',
            7: 'encargado_de',
        }

        order_index = _as_int(request.POST.get('order[0][column]'), 0)
        order_dir = request.POST.get('order[0][dir]', 'asc')

        campo = columnas.get(order_index, 'anexo')

        if order_dir == 'desc':
            campo = f'-{campo}'

        queryset = queryset.order_by(campo, 'pk')

        # Total después de filtrar
        records_filtered = queryset.count()

        # Paginación
        if length != -1:
            queryset = queryset[start:start + length]

        data = list(queryset.values(
            'id',
            'anexo',
            'anexo_publico',
            'numero_telefonico',
            'nombre_anexo',
            'email',
            'unidad_organizacional__nombre',
            'unidad_organizacional__direccion__nombre',
            'unidad_organizacional__direccion__enlace_google_maps',
            'encargado_de',
        ))

        deptos_qs = UnidadOrganizacional.objects.filter(
            establecimiento_id=establecimiento_id,
            es_departamento=True,
        )
        if unidades_permitidas_ids:
            deptos_qs = deptos_qs.filter(id__in=unidades_permitidas_ids)

        opciones_departamentos = [
            {
                'label': departamento.nombre,
                'value': departamento.nombre
            }
            for departamento in deptos_qs.order_by('nombre')
        ]

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
            'columnControl': {
                'unidad_organizacional__nombre': opciones_departamentos
            }
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated and self.request.user.establecimiento:
            establecimiento = self.request.user.establecimiento
        else:
            establecimiento_id = _as_int(
                self.request.GET.get('establecimiento'), 1
            )
            establecimiento = Establecimiento.objects.filter(
                pk=establecimiento_id
            ).first()
            if establecimiento is None:
                establecimiento = get_object_or_404(Establecimiento, pk=1)

        context['establecimiento'] = establecimiento
        return context


class UnidadesPerfilAgendaMixin:
    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        unidades = UnidadOrganizacional.objects.none()

        if self.request.user.is_authenticated:
            perfil = PerfilAgenda.objects.filter(
                usuario=self.request.user,
                is_active=True,
            ).first()

            if perfil:
                unidades = perfil.unidad_organizacional.all()

        form.fields['unidad_organizacional'].queryset = unidades

        return form


@method_decorator(user_editor_module, name='dispatch')
class AnexosCreateView(UnidadesPerfilAgendaMixin, StandardCreateView):
    template_name = 'anexos/form_anexos.html'
    model = Anexo
    form_class = FormAnexos
    title = 'Nuevo Anexo'
    success_url = reverse_lazy('agenda:list_anexos_edit')

    def get_list_url(self):
        return reverse_lazy('agenda:list_anexos_edit')


@method_decorator(user_editor_module, name='dispatch')
class AnexosUpdateView(UnidadesPerfilAgendaMixin, StandardUpdateView):
    template_name = 'anexos/form_anexos.html'
    model = Anexo
    form_class = FormAnexos
    title = 'Editar Anexo'
    success_url = reverse_lazy('agenda:list_anexos_edit')

    def get_list_url(self):
        return reverse_lazy('agenda:list_anexos_edit')


@user_editor_module
@require_POST
def anexos_eliminar(request, pk):
    """
    Vista basada en función para eliminar un anexo mediante petición AJAX.
    Aplica borrado lógico (is_active = False) o eliminación física según el modelo,
    y retorna una respuesta en formato JSON para SweetAlert2.
    """
    try:
        anexo = get_object_or_404(Anexo, pk=pk)
        nombre = str(anexo.nombre_anexo or anexo.anexo or f"Anexo #{anexo.pk}")

        if hasattr(anexo, 'is_active'):
            anexo.is_active = False
            if hasattr(anexo, 'updated_by'):
                anexo.updated_by = request.user
            anexo.save()
        else:
            anexo.delete()

        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': f'El anexo "{nombre}" (ID: {pk}) fue eliminado correctamente.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': f'Ocurrió un error al intentar eliminar el registro: {str(e)}'
        }, status=400)


@user_editor_module
def anexos_pdf_view(request):
    from core.models.unidad_organizacional import UnidadOrganizacional
    # Obtener anexos activos y agruparlos por unidad organizacional (departamento)

    # Optimizamos la consulta
    queryset = Anexo.objects.filter(is_active=True)
    if request.user.establecimiento:
        queryset = queryset.filter(establecimiento=request.user.establecimiento)

    anexos = queryset.select_related(
        'funcionario', 'funcionario__unidad_organizacional', 'unidad_organizacional', 'rol_organizacional',
        'funcionario__rol_organizacional'
    ).order_by('funcionario__unidad_organizacional__nombre', 'unidad_organizacional__nombre', 'funcionario__nombres',
               'nombre_anexo')

    # Mapeo de todas las UOs para encontrar departamentos eficientemente sin N+1
    all_uos = {u.id: u for u in UnidadOrganizacional.objects.all()}

    def get_main_department(uo):
        if not uo:
            return None
        # Usamos la unidad del mapa para asegurar acceso a los campos necesarios
        curr = all_uos.get(uo.id) or uo

        # Buscamos el departamento de mayor nivel (el más cercano a la raíz)
        top_depto = None
        temp = curr
        while temp:
            if temp.es_departamento:
                top_depto = temp
            if not temp.padre_id:
                # Si llegamos a la raíz y no hay nada marcado como depto, la raíz es el depto
                if not top_depto:
                    top_depto = temp
                break
            temp = all_uos.get(temp.padre_id)
        return top_depto

    # Lista de colores pasteles
    pastel_colors = [
        '#FFD1DC', '#FFB7B2', '#FFDAC1', '#E2F0CB', '#B5EAD7', '#C7CEEA',
        '#F3FFE3', '#E0BBE4', '#CFD8DC', '#FFF9C4', '#F1F8E9', '#E1F5FE'
    ]

    # Agrupar por departamento
    unidades_dict = {}
    color_index = 0
    for anexo in anexos:
        # Prioridad a la unidad del funcionario
        uo = anexo.funcionario.unidad_organizacional if anexo.funcionario else anexo.unidad_organizacional

        depto = get_main_department(uo)
        # Usamos el nombre para la clave de agrupación para asegurar que nombres idénticos se junten
        # pero incluimos el ID en el objeto para mantener referencias si fuera necesario
        depto_id = depto.id if depto else 0
        depto_nombre = depto.nombre if depto else "SIN UNIDAD"

        if depto_nombre not in unidades_dict:
            unidades_dict[depto_nombre] = {
                'id': depto_id,
                'nombre': depto_nombre,
                'anexos_list': [],
                'color': pastel_colors[color_index % len(pastel_colors)]
            }
            color_index += 1
        unidades_dict[depto_nombre]['anexos_list'].append(anexo)

    # Convertir a lista y ordenar por nombre de departamento
    unidades = sorted(unidades_dict.values(), key=lambda x: x['nombre'])

    # Renderizar el HTML
    html_string = render_to_string('anexos/anexos_pdf.html', {
        'unidades': unidades,
        'request': request,
    })

    # Crear el PDF
    base_url = request.build_absolute_uri('/')
    html = HTML(string=html_string, base_url=base_url)
    pdf = html.write_pdf()

    # Devolver el PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="listado_anexos.pdf"'

    return response
