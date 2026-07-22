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
from django.views.generic import ListView, CreateView, UpdateView
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
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')

        queryset = Anexo.objects.select_related(
            'funcionario',
            'funcionario__unidad_organizacional',
            'funcionario__unidad_organizacional__direccion',
            'funcionario__profesion',
            'funcionario__rol_organizacional',
            'rol_organizacional',
            'unidad_organizacional'
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

        data = []
        for a in queryset:
            if a.funcionario:
                # Caso con funcionario
                uo = a.funcionario.unidad_organizacional
                uo_text = uo.nombre if uo else "-"
                nombres_text = f"{a.funcionario.nombres or '-'} {a.funcionario.apellidos or '-'}"
                email_text = a.funcionario.email or "-"
                rol_text = a.funcionario.rol_organizacional.nombre if a.funcionario.rol_organizacional else "-"
                cargo_text = a.funcionario.cargo if a.funcionario.cargo else "-"
                url_editar = reverse('agenda:anexo_editar', args=[a.id])
            else:
                # Caso sin funcionario
                uo = a.unidad_organizacional
                uo_text = uo.nombre if uo else "-"
                nombres_text = a.nombre_anexo or "-"
                email_text = a.email or "-"
                rol_text = a.rol_organizacional.nombre if a.rol_organizacional else "-"
                cargo_text = a.encargado_de or "-"
                url_editar = reverse('agenda:anexo_sin_funcionario_editar', args=[a.id])

            data.append({
                "anexo": a.anexo,
                "publico": a.anexo_publico or "-",
                "telefono": a.numero_telefonico or "-",
                "nombres": nombres_text,
                "email": email_text,
                "unidad": uo_text,
                "rol_organizacional": rol_text,
                "cargo": cargo_text,

                "acciones": f"""
                    <div class="text-center">
                        <a href="{url_editar}" class="btn btn-sm btn-primary">
                            <i class="fas fa-edit"></i>
                        </a>
                        <button class="btn btn-sm btn-danger" onclick="confirmarEliminar({a.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                """
            })

        return JsonResponse({
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": total_filtered,
            "data": data,
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


class AnexoListView(ListView):
    model = Anexo
    template_name = "anexos/list_anexos.html"
    context_object_name = "anexos"
    paginate_by = 10

    def get_queryset(self):
        establecimiento_id = self.request.GET.get("establecimiento")
        if self.request.user.is_authenticated:

            if establecimiento_id:
                queryset = self.model.objects.filter(establecimiento_id=establecimiento_id)
            else:
                establecimiento = getattr(self.request.user, "establecimiento", None)
                queryset = self.model.objects.filter(establecimiento=establecimiento)
        else:
            obj = Establecimiento.objects.order_by('id').first()
            queryset = self.model.objects.filter(establecimiento=obj.id)

        queryset = queryset.select_related(
            "establecimiento",
            "funcionario",
            "funcionario__unidad_organizacional",
            "funcionario__profesion",
            "unidad_organizacional",
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
        context["establecimiento_select"] = Establecimiento.objects.filter(
            pk=self.request.GET.get("establecimiento")).first()
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


class AnexoEditListView(LoginRequiredMixin, ListView):
    model = Anexo
    template_name = "anexos/list_anexos_edit.html"
    context_object_name = "anexos"
    paginate_by = 10

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
                "unidad_organizacional"
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
