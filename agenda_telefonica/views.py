from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from weasyprint import HTML

from agenda_telefonica.decorators import user_editor_module
from agenda_telefonica.forms import AnexoFuncionarioForm, AnexoFilterForm, AnexoSinFuncionarioForm
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

    if unidad_organizacional_id:
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
        form = AnexoFuncionarioForm(request.POST, instance=anexo_instance, user=request.user)
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
        form = AnexoFuncionarioForm(instance=anexo_instance, user=request.user)

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
        ).all()

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

    return render(request, 'anexos/anexos_form.html', {
        'form': form,
        'is_edit': pk is not None
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


def eliminar_anexo(request, pk):
    anexo = get_object_or_404(Anexo, pk=pk)
    with transaction.atomic():
        anexo.delete()
    messages.info(request, "Anexo eliminado y funcionario desactivado correctamente.")
    return redirect('agenda:anexos')


@user_editor_module
def anexos_pdf_view(request):
    # Obtener anexos activos y agruparlos por unidad organizacional

    # Optimizamos la consulta
    anexos = Anexo.objects.filter(is_active=True).select_related(
        'funcionario', 'funcionario__unidad_organizacional', 'unidad_organizacional', 'rol_organizacional',
        'funcionario__rol_organizacional'
    ).order_by('funcionario__unidad_organizacional__nombre', 'unidad_organizacional__nombre', 'funcionario__nombres',
               'nombre_anexo')

    # Lista de colores pasteles
    pastel_colors = [
        '#FFD1DC', '#FFB7B2', '#FFDAC1', '#E2F0CB', '#B5EAD7', '#C7CEEA',
        '#F3FFE3', '#E0BBE4', '#CFD8DC', '#FFF9C4', '#F1F8E9', '#E1F5FE'
    ]

    # Agrupar por unidad
    unidades_dict = {}
    color_index = 0
    for anexo in anexos:
        if anexo.funcionario:
            uo = anexo.funcionario.unidad_organizacional
        else:
            uo = anexo.unidad_organizacional

        uo_id = uo.id if uo else 0
        uo_nombre = uo.nombre if uo else "SIN UNIDAD"

        if uo_id not in unidades_dict:
            unidades_dict[uo_id] = {
                'nombre': uo_nombre,
                'anexos_list': [],
                'color': pastel_colors[color_index % len(pastel_colors)]
            }
            color_index += 1
        unidades_dict[uo_id]['anexos_list'].append(anexo)

    # Convertir a lista para el template
    unidades = list(unidades_dict.values())

    # Renderizar el HTML
    html_string = render_to_string('anexos/anexos_pdf.html', {'unidades': unidades})

    # Crear el PDF
    html = HTML(string=html_string)
    pdf = html.write_pdf()

    # Devolver el PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="listado_anexos.pdf"'

    return response
