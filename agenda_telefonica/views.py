from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from weasyprint import HTML

from agenda_telefonica.decorators import user_editor_module, user_mantenedores_module
from agenda_telefonica.filters import AnexoFilter, AnexoEditFilter
from agenda_telefonica.forms import (
    AnexoFilterForm,
    AnexoFuncionarioCompletoForm,
    AnexoSinFuncionarioForm,
)
from agenda_telefonica.models import Anexo
from core.models import Establecimiento
from core.models.funcionario import Funcionario
from core.models.unidad_organizacional import UnidadOrganizacional


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _format_unidad_jerarquia(unidad):
    if not unidad:
        return []
    return [str(item) for item in unidad.get_jerarquia_reducida_invertida()]


def serialize_anexo(anexo, include_actions=False, include_status=False):
    funcionario = anexo.funcionario

    if funcionario:
        unidad = funcionario.unidad_organizacional
        rol = funcionario.rol_organizacional
        nombres = " ".join(
            value for value in [funcionario.nombres, funcionario.apellidos] if value
        ) or None
        email = funcionario.email
        cargo = funcionario.cargo
        editar_url = reverse("agenda:anexo_editar", args=[anexo.pk])
    else:
        unidad = anexo.unidad_organizacional
        rol = anexo.rol_organizacional
        nombres = anexo.nombre_anexo
        email = anexo.email
        cargo = anexo.encargado_de
        editar_url = reverse("agenda:anexo_sin_funcionario_editar", args=[anexo.pk])

    direccion = unidad.direccion if unidad else None

    data = {
        "id": anexo.pk,
        "anexo": anexo.anexo,
        "anexo_publico": anexo.anexo_publico,
        "publico": anexo.anexo_publico,
        "numero_telefonico": anexo.numero_telefonico,
        "telefono": anexo.numero_telefonico,
        "nombres": nombres,
        "email": email,
        "unidad_organizacional": _format_unidad_jerarquia(unidad),
        "unidad": " / ".join(_format_unidad_jerarquia(unidad)) or None,
        "direccion": direccion.nombre if direccion else None,
        "direccion_url": direccion.enlace_google_maps if direccion else None,
        "rol_organizacional": str(rol) if rol else None,
        "cargo": cargo,
        "created_at": anexo.created_at.isoformat() if anexo.created_at else None,
        "updated_at": anexo.updated_at.isoformat() if anexo.updated_at else None,
    }

    if include_status:
        data["is_active"] = anexo.is_active

    if include_actions:
        eliminar_url = reverse("agenda:anexo_delete", args=[anexo.pk])
        data.update({
            "tiene_funcionario": bool(funcionario),
            "editar_url": editar_url,
            "eliminar_url": eliminar_url,
            "acciones": (
                f'<div class="text-center">'
                f'<a href="{editar_url}" class="btn btn-sm btn-primary" title="Editar">'
                f'<i class="bi bi-pencil"></i>'
                f'</a>'
                f'</div>'
            ),
        })

    return data


class AnexoDataTableMixin:
    max_page_length = 100

    columns = [
        "anexo",
        "anexo_publico",
        "numero_telefonico",
        "funcionario__nombres",
        "funcionario__email",
        "funcionario__unidad_organizacional__nombre",
        "funcionario__unidad_organizacional__direccion__nombre",
        "funcionario__rol_organizacional__nombre",
        "funcionario__cargo",
    ]

    column_search_map = {
        0: ["anexo"],
        1: ["anexo_publico"],
        2: ["numero_telefonico"],
        3: ["funcionario__nombres", "funcionario__apellidos", "nombre_anexo"],
        4: ["funcionario__email", "email"],
        5: ["funcionario__unidad_organizacional__nombre", "unidad_organizacional__nombre"],
        6: [
            "funcionario__unidad_organizacional__direccion__nombre",
            "unidad_organizacional__direccion__nombre",
        ],
        7: ["funcionario__rol_organizacional__nombre", "rol_organizacional__nombre"],
        8: ["funcionario__cargo", "encargado_de"],
    }

    searchable_columns = [
        "anexo",
        "anexo_publico",
        "numero_telefonico",
        "nombre_anexo",
        "email",
        "encargado_de",
        "rol_organizacional__nombre",
        "unidad_organizacional__nombre",
        "unidad_organizacional__direccion__nombre",
        "funcionario__rut",
        "funcionario__nombres",
        "funcionario__apellidos",
        "funcionario__email",
        "funcionario__cargo",
        "funcionario__rol_organizacional__nombre",
        "funcionario__unidad_organizacional__nombre",
        "funcionario__unidad_organizacional__direccion__nombre",
    ]

    include_actions = False
    include_status = False

    def get(self, request, *args, **kwargs):
        if self.is_datatables_request(request):
            return self.datatables_response(request)
        return super().get(request, *args, **kwargs)

    @staticmethod
    def is_datatables_request(request):
        return (
                request.headers.get("X-Requested-With") == "XMLHttpRequest"
                or "draw" in request.GET
        )

    def datatables_response(self, request):
        queryset = self.get_queryset()

        draw = max(_as_int(request.GET.get("draw"), 1), 1)
        start = max(_as_int(request.GET.get("start"), 0), 0)
        length = _as_int(request.GET.get("length"), 10)
        if length < 1 or length > self.max_page_length:
            length = self.max_page_length

        records_total = queryset.count()
        queryset = self.apply_datatables_search(queryset, request)
        records_filtered = queryset.count()
        queryset = self.apply_datatables_ordering(queryset, request)
        queryset = queryset[start:start + length]

        return JsonResponse({
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": [
                serialize_anexo(
                    anexo,
                    include_actions=self.include_actions,
                    include_status=self.include_status,
                )
                for anexo in queryset
            ],
        })

    def apply_datatables_search(self, queryset, request):
        search_value = request.GET.get("search[value]", "").strip()

        if search_value:
            search_query = Q()
            for column in self.searchable_columns:
                search_query |= Q(**{f"{column}__icontains": search_value})
            queryset = queryset.filter(search_query)

        for index, fields in self.column_search_map.items():
            value = request.GET.get(f"columns[{index}][search][value]", "").strip()
            if not value:
                continue

            column_query = Q()
            for field in fields:
                column_query |= Q(**{f"{field}__icontains": value})
            queryset = queryset.filter(column_query)

        return queryset

    def apply_datatables_ordering(self, queryset, request):
        order_column = request.GET.get("order[0][column]")
        order_dir = request.GET.get("order[0][dir]", "asc")

        if order_dir not in {"asc", "desc"}:
            order_dir = "asc"

        try:
            column_index = int(order_column)
        except (TypeError, ValueError):
            return queryset

        if 0 <= column_index < len(self.columns):
            field = self.columns[column_index]
            if field:
                if order_dir == "desc":
                    field = f"-{field}"
                return queryset.order_by(field)

        return queryset


def index(request):
    establecimiento_id = request.GET.get('establecimiento')
    establecimiento = None
    if establecimiento_id:
        establecimiento = get_object_or_404(Establecimiento, id=establecimiento_id)

    form = AnexoFilterForm(request.GET or None, establecimiento=establecimiento_id)
    return render(request, 'anexos/index.html', {
        'form': form,
        'establecimiento_id': establecimiento_id,
        'establecimiento': establecimiento
    })


def buscar_anexo(request):
    search_value = request.GET.get('q', '')
    establecimiento_id = request.GET.get('establecimiento')
    per_page = request.GET.get('per_page', 10)
    unidad_organizacional_id = request.GET.get('unidad_organizacional')
    subdepartamento_id = request.GET.get('subdepartamento')

    queryset = Anexo.objects.select_related(
        'funcionario',
        'funcionario__unidad_organizacional',
        'funcionario__unidad_organizacional__direccion',
        'funcionario__profesion',
        'funcionario__rol_organizacional',
        'rol_organizacional',
        'unidad_organizacional',
        'unidad_organizacional__direccion'
    ).all()

    if establecimiento_id:
        queryset = queryset.filter(establecimiento_id=establecimiento_id)

    if subdepartamento_id:
        from core.models.unidad_organizacional import UnidadOrganizacional
        subdepto = get_object_or_404(UnidadOrganizacional, id=subdepartamento_id)
        descendientes = subdepto.get_descendants(include_self=True).filter(is_active=True)
        queryset = queryset.filter(
            Q(funcionario__unidad_organizacional__in=descendientes) |
            Q(unidad_organizacional__in=descendientes)
        )
    elif unidad_organizacional_id:
        # Filtrar por la unidad seleccionada y todas sus descendientes
        from core.models.unidad_organizacional import UnidadOrganizacional
        unidad = get_object_or_404(UnidadOrganizacional, id=unidad_organizacional_id)
        descendientes = unidad.get_descendants(include_self=True).filter(is_active=True)
        queryset = queryset.filter(
            Q(funcionario__unidad_organizacional__in=descendientes) |
            Q(unidad_organizacional__in=descendientes)
        )

    if search_value:
        queryset = queryset.filter(
            Q(anexo__icontains=search_value) |
            Q(anexo_publico__icontains=search_value) |
            Q(numero_telefonico__icontains=search_value) |
            Q(nombre_anexo__icontains=search_value) |
            Q(email__icontains=search_value) |
            Q(encargado_de__icontains=search_value) |
            Q(rol_organizacional__nombre__icontains=search_value) |
            Q(unidad_organizacional__nombre__icontains=search_value) |
            Q(funcionario__rut__icontains=search_value) |
            Q(funcionario__nombres__icontains=search_value) |
            Q(funcionario__apellidos__icontains=search_value) |
            Q(funcionario__email__icontains=search_value) |
            Q(funcionario__cargo__icontains=search_value) |
            Q(funcionario__rol_organizacional__nombre__icontains=search_value) |
            Q(funcionario__profesion__nombre__icontains=search_value) |
            Q(funcionario__unidad_organizacional__nombre__icontains=search_value)
        )

    # Filtrar solo activos por defecto para la vista pública
    queryset = queryset.filter(is_active=True)

    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'anexos/components/_table_result_public.html', {
        'page_obj': page_obj,
        'establecimiento_id': establecimiento_id,
    })


@user_editor_module
def anexos_view(request, pk=None):
    if pk:
        anexo_instance = get_object_or_404(Anexo, pk=pk)
    else:
        anexo_instance = None

    if request.method == 'POST':
        form = AnexoFuncionarioCompletoForm(request.POST, instance=anexo_instance, user=request.user)
        if form.is_valid():
            rut = form.cleaned_data.get('rut').upper()
            nombres = form.cleaned_data.get('nombres').title()
            apellidos = form.cleaned_data.get('apellidos').title()
            email = form.cleaned_data.get('email')
            cargo = form.cleaned_data.get('cargo')
            profesion = form.cleaned_data.get('profesion')
            unidad_organizacional = form.cleaned_data.get('unidad_organizacional')
            rol_organizacional = form.cleaned_data.get('rol_organizacional')

            # Buscar o crear/actualizar funcionario
            funcionario_defaults = {
                'nombres': nombres,
                'apellidos': apellidos,
                'email': email,
                'nombre': f"{nombres} {apellidos}",
                'cargo': cargo,
                'profesion': profesion,
                'unidad_organizacional': unidad_organizacional,
                'rol_organizacional': rol_organizacional,
                'updated_by': request.user,
            }
            if request.user.establecimiento:
                funcionario_defaults['establecimiento'] = request.user.establecimiento

            funcionario, created = Funcionario.objects.update_or_create(
                rut=rut,
                defaults=funcionario_defaults
            )
            if created:
                funcionario.created_by = request.user
                funcionario.save()

            anexo = form.save(commit=False)
            anexo.funcionario = funcionario
            anexo.unidad_organizacional = unidad_organizacional
            if request.user.establecimiento:
                anexo.establecimiento = request.user.establecimiento

            if not anexo.pk:
                anexo.created_by = request.user
            anexo.updated_by = request.user

            anexo.save()

            if pk:
                messages.success(request, "Anexo actualizado correctamente.")
            else:
                messages.success(request, "Anexo creado correctamente.")

            return redirect('agenda:anexos')
    else:
        form = AnexoFuncionarioCompletoForm(instance=anexo_instance, user=request.user)

    # Lógica para DataTables AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('draw'):
        endpoint = AnexoDataTableMixin()
        endpoint.include_actions = True
        draw = max(_as_int(request.GET.get("draw"), 1), 1)
        start = max(_as_int(request.GET.get("start"), 0), 0)
        length = _as_int(request.GET.get("length"), 10)
        if length < 1 or length > endpoint.max_page_length:
            length = endpoint.max_page_length
        search_value = request.GET.get('search[value]', '')

        queryset = Anexo.objects.select_related(
            'funcionario',
            'funcionario__unidad_organizacional',
            'funcionario__unidad_organizacional__padre',
            'funcionario__unidad_organizacional__padre__padre',
            'funcionario__unidad_organizacional__direccion',
            'funcionario__profesion',
            'funcionario__rol_organizacional',
            'rol_organizacional',
            'unidad_organizacional',
            'unidad_organizacional__padre',
            'unidad_organizacional__padre__padre',
            'unidad_organizacional__direccion',
        )

        if request.user.establecimiento:
            queryset = queryset.filter(establecimiento=request.user.establecimiento)

        queryset = queryset.all()

        total_records = queryset.count()

        if search_value:
            queryset = queryset.filter(
                Q(anexo__icontains=search_value) |
                Q(anexo_publico__icontains=search_value) |
                Q(numero_telefonico__icontains=search_value) |
                Q(nombre_anexo__icontains=search_value) |
                Q(email__icontains=search_value) |
                Q(encargado_de__icontains=search_value) |
                Q(rol_organizacional__nombre__icontains=search_value) |
                Q(unidad_organizacional__nombre__icontains=search_value) |
                Q(funcionario__rut__icontains=search_value) |
                Q(funcionario__nombres__icontains=search_value) |
                Q(funcionario__apellidos__icontains=search_value) |
                Q(funcionario__email__icontains=search_value) |
                Q(funcionario__cargo__icontains=search_value) |
                Q(funcionario__rol_organizacional__nombre__icontains=search_value) |
                Q(funcionario__profesion__nombre__icontains=search_value) |
                Q(funcionario__unidad_organizacional__nombre__icontains=search_value)
            )

        # Ordenamiento
        order_column_index = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]', 'asc')
        columns = [
            'anexo', 'anexo_publico', 'numero_telefonico',
            'funcionario__nombres', 'funcionario__email', 'funcionario__unidad_organizacional__nombre',
            'funcionario__rol_organizacional__nombre', 'funcionario__cargo', 'acciones'
        ]

        if order_column_index:
            try:
                col_name = columns[int(order_column_index)]
                if order_dir == 'desc':
                    col_name = '-' + col_name
                queryset = queryset.order_by(col_name)
            except (IndexError, ValueError):
                pass

        total_filtered = queryset.count()

        # El usuario pidió un máximo de 100 registros para la visualización inicial/por búsqueda
        if length == -1 or length > 100:
            length = 100

        queryset = queryset[start:start + length]

        return JsonResponse({
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": total_filtered,
            "data": [
                serialize_anexo(anexo, include_actions=True)
                for anexo in queryset
            ],
        })

    return render(request, 'anexos/form_anexos.html', {
        'form': form,
        'is_edit': pk is not None,
        'page_title': 'Editar anexo' if pk else 'Nuevo anexo',
        'submit_label': 'Actualizar' if pk else 'Guardar',
    })


@user_editor_module
def anexos_sin_funcionario_view(request, pk=None):
    if pk:
        anexo_instance = get_object_or_404(Anexo, pk=pk)
    else:
        anexo_instance = None

    if request.method == 'POST':
        form = AnexoSinFuncionarioForm(request.POST, instance=anexo_instance, user=request.user)
        if form.is_valid():
            unidad_organizacional = form.cleaned_data.get('unidad_organizacional')
            anexo = form.save(commit=False)
            anexo.unidad_organizacional = unidad_organizacional
            if request.user.establecimiento:
                anexo.establecimiento = request.user.establecimiento

            if not anexo.pk:
                anexo.created_by = request.user
            anexo.updated_by = request.user

            anexo.save()

            if pk:
                messages.success(request, "Anexo sin funcionario actualizado correctamente.")
            else:
                messages.success(request, "Anexo sin funcionario creado correctamente.")

            return redirect('agenda:anexos_sin_funcionario')
    else:
        form = AnexoSinFuncionarioForm(instance=anexo_instance, user=request.user)

    # Lógica para DataTables AJAX (Reutilizamos la lógica de anexos_view)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('draw'):
        return anexos_view(request, pk)

    return render(request, 'anexos/anexos_form_sin_funcionario.html', {
        'form': form,
        'is_edit': pk is not None
    })


@login_required
@require_POST
def anexo_delete_view(request, pk):
    anexo = get_object_or_404(Anexo, pk=pk)
    with transaction.atomic():
        if anexo.funcionario:
            anexo.funcionario.is_active = False
            anexo.funcionario.save()
        anexo.delete()

    messages.success(request, "Anexo eliminado correctamente.")
    return redirect("agenda:list_anexos_edit")


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


class AnexoListView(AnexoDataTableMixin, ListView):
    model = Anexo
    template_name = "anexos/list_anexos.html"
    context_object_name = "anexos"
    paginate_by = 10

    def get_queryset(self):
        establecimiento_id = self.request.GET.get("establecimiento")

        if establecimiento_id:
            queryset = self.model.objects.filter(establecimiento_id=establecimiento_id)
        else:
            establecimiento = Establecimiento.objects.order_by("id").first()
            queryset = self.model.objects.filter(establecimiento=establecimiento)

        queryset = queryset.select_related(
            "establecimiento",
            "funcionario",
            "funcionario__unidad_organizacional",
            "funcionario__unidad_organizacional__padre",
            "funcionario__unidad_organizacional__padre__padre",
            "funcionario__unidad_organizacional__direccion",
            "funcionario__profesion",
            "funcionario__rol_organizacional",
            "rol_organizacional",
            "unidad_organizacional",
            "unidad_organizacional__padre",
            "unidad_organizacional__padre__padre",
            "unidad_organizacional__direccion",
        )

        self.filter_form = AnexoFilter(self.request.GET)

        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data

            if data["anexo"]:
                queryset = queryset.filter(anexo__icontains=data["anexo"])

            if data["anexo_publico"]:
                queryset = queryset.filter(anexo_publico__icontains=data["anexo_publico"])

            if data["numero_telefonico"]:
                queryset = queryset.filter(numero_telefonico__icontains=data["numero_telefonico"])

            if data["nombre"]:
                queryset = queryset.filter(
                    Q(funcionario__nombres__icontains=data["nombre"])
                    | Q(funcionario__apellidos__icontains=data["nombre"])
                    | Q(nombre_anexo__icontains=data["nombre"])
                )

            if data["email"]:
                queryset = queryset.filter(
                    Q(funcionario__email__icontains=data["email"]) | Q(email__icontains=data["email"])
                )

            if data["cargo"]:
                queryset = queryset.filter(
                    Q(funcionario__cargo__icontains=data["cargo"]) | Q(encargado_de__icontains=data["cargo"])
                )

            if data["rol_organizacional"]:
                queryset = queryset.filter(
                    Q(funcionario__rol_organizacional=data["rol_organizacional"])
                    | Q(rol_organizacional=data["rol_organizacional"])
                )

            if data.get("subdepartamento"):
                descendientes = data["subdepartamento"].get_descendants(include_self=True)
                queryset = queryset.filter(
                    Q(funcionario__unidad_organizacional__in=descendientes)
                    | Q(unidad_organizacional__in=descendientes)
                )
            elif data.get("unidad_organizacional"):
                # Filtrar por la unidad seleccionada y todas sus descendientes
                descendientes = data["unidad_organizacional"].get_descendants(include_self=True)
                queryset = queryset.filter(
                    Q(funcionario__unidad_organizacional__in=descendientes)
                    | Q(unidad_organizacional__in=descendientes)
                )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        establecimiento_id = self.request.GET.get("establecimiento")
        if establecimiento_id:
            context["establecimiento_select"] = Establecimiento.objects.filter(pk=establecimiento_id).first()
        else:
            context["establecimiento_select"] = Establecimiento.objects.order_by("id").first()
        return context


class AnexoBaseFormView:
    model = Anexo
    form_class = AnexoFuncionarioCompletoForm
    template_name = "anexos/form_anexos.html"
    success_url = reverse_lazy("agenda:list_anexos_edit")
    page_title = "Formulario Anexo"
    submit_label = "Guardar"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["submit_label"] = self.submit_label
        context["is_edit"] = isinstance(self, UpdateView)
        return context


class AnexoCreateView(LoginRequiredMixin, AnexoBaseFormView, CreateView):
    page_title = "Nuevo funcionario"
    submit_label = "Crear"

    def form_valid(self, form):
        establecimiento = getattr(self.request.user, "establecimiento", None)
        if not establecimiento:
            form.add_error(
                None,
                "No se pudo asignar el establecimiento del usuario autenticado.",
            )
            return self.form_invalid(form)

        from core.models.funcionario import Funcionario
        from django.db import transaction

        try:
            with transaction.atomic():
                rut = form.cleaned_data.get("rut").upper()
                funcionario, created = Funcionario.objects.get_or_create(
                    rut=rut,
                    defaults={
                        "establecimiento": establecimiento,
                        "created_by": self.request.user,
                        "updated_by": self.request.user
                    }
                )

                # Actualizar datos del funcionario (siempre, según requerimiento)
                funcionario.nombres = form.cleaned_data.get("nombres")
                funcionario.apellidos = form.cleaned_data.get("apellidos")
                funcionario.email = form.cleaned_data.get("email")
                funcionario.cargo = form.cleaned_data.get("cargo")
                funcionario.profesion = form.cleaned_data.get("profesion")
                funcionario.rol_organizacional = form.cleaned_data.get("rol_organizacional")
                funcionario.unidad_organizacional = form.cleaned_data.get("unidad_organizacional")
                funcionario.updated_by = self.request.user
                funcionario.save()

                form.instance.funcionario = funcionario
                form.instance.establecimiento = establecimiento
                form.instance.created_by = self.request.user
                form.instance.updated_by = self.request.user

                response = super().form_valid(form)
                messages.success(self.request, "Anexo creado correctamente.")
                return response
        except Exception as e:
            form.add_error(None, f"Error al procesar el anexo: {str(e)}")
            return self.form_invalid(form)


class AnexoUpdateView(LoginRequiredMixin, AnexoBaseFormView, UpdateView):
    page_title = "Editar funcionario"
    submit_label = "Actualizar"

    def form_valid(self, form):
        establecimiento = getattr(self.request.user, "establecimiento", None)
        if establecimiento:
            form.instance.establecimiento = establecimiento

        from django.db import transaction

        try:
            with transaction.atomic():
                funcionario = form.instance.funcionario
                if funcionario:
                    # Actualizar datos del funcionario
                    funcionario.rut = form.cleaned_data.get("rut").upper()
                    funcionario.nombres = form.cleaned_data.get("nombres")
                    funcionario.apellidos = form.cleaned_data.get("apellidos")
                    funcionario.email = form.cleaned_data.get("email")
                    funcionario.cargo = form.cleaned_data.get("cargo")
                    funcionario.profesion = form.cleaned_data.get("profesion")
                    funcionario.rol_organizacional = form.cleaned_data.get("rol_organizacional")
                    funcionario.unidad_organizacional = form.cleaned_data.get("unidad_organizacional")
                    funcionario.updated_by = self.request.user
                    funcionario.save()

                form.instance.updated_by = self.request.user
                response = super().form_valid(form)
                messages.success(self.request, "Anexo actualizado correctamente.")
                return response
        except Exception as e:
            form.add_error(None, f"Error al actualizar el anexo: {str(e)}")
            return self.form_invalid(form)


class AnexoEditListView(AnexoDataTableMixin, LoginRequiredMixin, ListView):
    model = Anexo
    template_name = "anexos/list_anexos_edit.html"
    context_object_name = "anexos"
    paginate_by = 10
    include_actions = True
    include_status = True
    columns = AnexoDataTableMixin.columns + ["is_active", None]
    column_search_map = AnexoDataTableMixin.column_search_map.copy()

    def get_queryset(self):
        establecimiento = self.request.user.establecimiento

        queryset = (
            super()
            .get_queryset()
            .filter(establecimiento=establecimiento)
            .select_related(
                "establecimiento",
                "funcionario",
                "funcionario__unidad_organizacional",
                "funcionario__unidad_organizacional__padre",
                "funcionario__unidad_organizacional__padre__padre",
                "funcionario__unidad_organizacional__direccion",
                "funcionario__rol_organizacional",
                "rol_organizacional",
                "unidad_organizacional",
                "unidad_organizacional__padre",
                "unidad_organizacional__padre__padre",
                "unidad_organizacional__direccion"
            )
        )

        # Filtro por unidades organizacionales del PerfilAgenda
        if hasattr(self.request.user, 'perfilagenda'):
            unidades = self.request.user.perfilagenda.unidad_organizacional.all()
            if unidades.exists():
                queryset = queryset.filter(
                    Q(funcionario__unidad_organizacional__in=unidades) |
                    Q(unidad_organizacional__in=unidades)
                )

        self.filter_form = AnexoEditFilter(self.request.GET)

        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data

            if data["anexo"]:
                queryset = queryset.filter(anexo__icontains=data["anexo"])

            if data["anexo_publico"]:
                queryset = queryset.filter(anexo_publico__icontains=data["anexo_publico"])

            if data["numero_telefonico"]:
                queryset = queryset.filter(numero_telefonico__icontains=data["numero_telefonico"])

            if data["nombre"]:
                queryset = queryset.filter(
                    Q(funcionario__nombres__icontains=data["nombre"])
                    | Q(funcionario__apellidos__icontains=data["nombre"])
                    | Q(nombre_anexo__icontains=data["nombre"])
                )

            if data["email"]:
                queryset = queryset.filter(
                    Q(funcionario__email__icontains=data["email"]) | Q(email__icontains=data["email"])
                )

            if data["cargo"]:
                queryset = queryset.filter(
                    Q(funcionario__cargo__icontains=data["cargo"]) | Q(encargado_de__icontains=data["cargo"])
                )

            if data["rol_organizacional"]:
                queryset = queryset.filter(
                    Q(funcionario__rol_organizacional=data["rol_organizacional"])
                    | Q(rol_organizacional=data["rol_organizacional"])
                )

            if data.get("subdepartamento"):
                descendientes = data["subdepartamento"].get_descendants(include_self=True)
                queryset = queryset.filter(
                    Q(funcionario__unidad_organizacional__in=descendientes)
                    | Q(unidad_organizacional__in=descendientes)
                )
            elif data.get("unidad_organizacional"):
                # Filtrar por la unidad seleccionada y todas sus descendientes
                descendientes = data["unidad_organizacional"].get_descendants(include_self=True)
                queryset = queryset.filter(
                    Q(funcionario__unidad_organizacional__in=descendientes)
                    | Q(unidad_organizacional__in=descendientes)
                )

            if data["is_active"]:
                queryset = queryset.filter(is_active=(data["is_active"] == "True"))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filtrar las opciones de unidad_organizacional en el formulario de filtro
        if hasattr(self.request.user, 'perfilagenda'):
            unidades = self.request.user.perfilagenda.unidad_organizacional.all()
            if unidades.exists():
                self.filter_form.fields['unidad_organizacional'].queryset = unidades

        context["filter_form"] = self.filter_form
        context["establecimiento_select"] = Establecimiento.objects.filter(
            pk=self.request.GET.get("establecimiento")).first()
        return context


@login_required
@user_mantenedores_module
def mantenedores_list_view(request, tipo):
    from core.views.direccion import DireccionListView
    from core.views.unidad_organizacional import UnidadOrganizacionalListView
    if tipo == 'direccion':
        return DireccionListView.as_view()(request)
    elif tipo == 'servicio':
        return UnidadOrganizacionalListView.as_view()(request)
    else:
        raise Http404


@login_required
@user_mantenedores_module
def mantenedores_create_view(request, tipo):
    from core.views.direccion import DireccionCreateView
    from core.views.unidad_organizacional import UnidadOrganizacionalCreateView
    if tipo == 'direccion':
        return DireccionCreateView.as_view()(request)
    elif tipo == 'servicio':
        return UnidadOrganizacionalCreateView.as_view()(request)
    else:
        raise Http404


@login_required
@user_mantenedores_module
def mantenedores_update_view(request, tipo, pk):
    from core.views.direccion import DireccionUpdateView
    from core.views.unidad_organizacional import UnidadOrganizacionalUpdateView
    if tipo == 'direccion':
        return DireccionUpdateView.as_view()(request, pk=pk)
    elif tipo == 'servicio':
        return UnidadOrganizacionalUpdateView.as_view()(request, pk=pk)
    else:
        raise Http404


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
        length = int(request.POST.get('length', 10))

        establecimiento_id = _as_int(request.GET.get('establecimiento'), 1)

        if not Establecimiento.objects.filter(pk=establecimiento_id).exists():
            establecimiento_id = 1

        queryset = Anexo.objects.filter(
            establecimiento_id=establecimiento_id
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

        prefijo = 'columns[5][columnControl][list]'

        departamentos = []

        for key, values in request.POST.lists():
            if key == prefijo or key.startswith(prefijo + '['):
                departamentos.extend(values)

        if departamentos:
            queryset = queryset.filter(
                unidad_organizacional__nombre__in=departamentos,
                establecimiento=establecimiento_id
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
            UnidadOrganizacional.objects.filter(establecimiento=establecimiento_id).order_by('nombre')
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
