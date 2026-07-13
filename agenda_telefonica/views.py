from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from agenda_telefonica.decorators import user_editor_module
from agenda_telefonica.forms import AnexoFuncionarioForm
from agenda_telefonica.models import Anexo
from core.models.funcionario import Funcionario


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
            nombres = form.cleaned_data.get('nombres').upper()
            apellidos = form.cleaned_data.get('apellidos').upper()
            email = form.cleaned_data.get('email')
            cargo = form.cleaned_data.get('cargo')
            profesion = form.cleaned_data.get('profesion')
            unidad_organizacional = form.cleaned_data.get('unidad_organizacional')

            # Buscar o crear/actualizar funcionario
            funcionario, created = Funcionario.objects.update_or_create(
                rut=rut,
                defaults={
                    'nombres': nombres,
                    'apellidos': apellidos,
                    'email': email,
                    'nombre': f"{nombres} {apellidos}",
                    'establecimiento': request.user.establecimiento,
                    'cargo': cargo,
                    'profesion': profesion,
                    'unidad_organizacional': unidad_organizacional
                }
            )

            anexo = form.save(commit=False)
            anexo.funcionario = funcionario
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
            'funcionario__profesion',
            'funcionario__rol_organizacional'
        ).all()

        total_records = queryset.count()

        if search_value:
            queryset = queryset.filter(
                Q(anexo__icontains=search_value) |
                Q(anexo_publico__icontains=search_value) |
                Q(numero_telefonico__icontains=search_value) |
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
            # Preparar jerarquía de unidad
            uo = a.funcionario.unidad_organizacional
            uo_html = "-"
            if uo:
                depto = uo.get_departamento()
                subdepto = uo.get_subdepto()
                unidad = uo.nombre

                parts = []
                if depto: parts.append(depto)
                if subdepto and subdepto != depto: parts.append(subdepto)
                if unidad and unidad != depto and unidad != subdepto: parts.append(unidad)
                uo_html = "<br>".join(parts) if parts else "-"

            data.append({
                "anexo": a.anexo,
                "publico": a.anexo_publico or "-",
                "telefono": a.numero_telefonico or "-",
                "nombres": f"{a.funcionario.nombres or "-"} {a.funcionario.apellidos or "-"}",
                "email": a.funcionario.email or "-",
                "unidad": uo_html,
                "rol_organizacional": a.funcionario.rol_organizacional.nombre if a.funcionario.rol_organizacional else "-",
                "cargo": a.funcionario.cargo if a.funcionario.cargo else "-",

                "acciones": f"""
                    <div class="text-center">
                        <a href="{reverse('agenda:anexo_editar', args=[a.id])}" class="btn btn-sm btn-primary">
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


def eliminar_anexo(request, pk):
    anexo = get_object_or_404(Anexo, pk=pk)
    with transaction.atomic():
        anexo.delete()
    messages.info(request, "Anexo eliminado y funcionario desactivado correctamente.")
    return redirect('agenda:anexos')
