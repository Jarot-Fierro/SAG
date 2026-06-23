from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect

from agenda_telefonica.forms import AnexoFilterForm, FormAnexo
from agenda_telefonica.models import Anexo
from core.models import Establecimiento


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


@login_required
def editor(request):
    perfil = getattr(request.user, 'perfilagenda', None)
    if not perfil or not perfil.editor:
        return redirect('agenda:index')

    establecimiento_id = request.GET.get('establecimiento')
    establecimiento = None
    if establecimiento_id:
        establecimiento = get_object_or_404(Establecimiento, id=establecimiento_id)

    # El formulario de filtro para el editor debe estar limitado a los servicios del perfil
    form_filter = AnexoFilterForm(request.GET or None, establecimiento=establecimiento_id)
    form_filter.fields['servicio'].queryset = perfil.servicio.filter(is_active=True)

    # Formulario para creación (vacío)
    form_anexo = FormAnexo(servicios_disponibles=perfil.servicio.filter(is_active=True))

    return render(request, 'anexos/crud.html', {
        'form': form_filter,
        'form_anexo': form_anexo,
        'establecimiento_id': establecimiento_id,
        'establecimiento': establecimiento
    })


@login_required
def buscar_anexo_editor(request):
    perfil = getattr(request.user, 'perfilagenda', None)
    if not perfil or not perfil.editor:
        return HttpResponse(status=403)

    q = request.GET.get("q", "").strip()
    servicio_id = request.GET.get("servicio")
    establecimiento_id = request.GET.get("establecimiento")
    per_page = request.GET.get("per_page", 10)
    page_number = request.GET.get("page", 1)

    # Filtrar por los servicios permitidos en el perfil
    servicios_permitidos = perfil.servicio.all()
    queryset = Anexo.objects.filter(servicio__in=servicios_permitidos)

    if establecimiento_id:
        queryset = queryset.filter(servicio__establecimiento_id=establecimiento_id)

    if q:
        queryset = queryset.filter(
            Q(nombre__icontains=q) |
            Q(anexo__icontains=q) |
            Q(email__icontains=q)
        )

    if servicio_id:
        queryset = queryset.filter(servicio=servicio_id)

    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page_number)

    table_columns = [
        {'name': 'anexo', 'label': 'Anexo'},
        {'name': 'anexo_publico', 'label': 'Público'},
        {'name': 'nombre', 'label': 'Nombre'},
        {'name': 'servicio', 'label': 'Servicio'},
        {'name': 'email', 'label': 'Correo'},
        {'name': 'is_active', 'label': 'Estado', 'is_boolean': True},
    ]

    return render(
        request,
        'anexos/components/_table_result_editor.html',
        {
            "object_list": page_obj,
            "table_columns": table_columns,
            "establecimiento_id": establecimiento_id,
        },
    )


@login_required
def guardar_anexo(request, pk=None):
    perfil = getattr(request.user, 'perfilagenda', None)
    if not perfil or not perfil.editor:
        return HttpResponse(status=403)

    anexo = None
    if pk:
        anexo = get_object_or_404(Anexo, pk=pk)
        # Verificar que el anexo pertenezca a un servicio que el usuario puede editar
        if anexo.servicio not in perfil.servicio.all():
            return HttpResponse("No tiene permiso para editar este anexo", status=403)

    if request.method == 'POST':
        form = FormAnexo(request.POST, instance=anexo, servicios_disponibles=perfil.servicio.filter(is_active=True))
        if form.is_valid():
            nuevo_anexo = form.save(commit=False)
            if not pk:
                nuevo_anexo.created_by = request.user
                # Asignar establecimiento del servicio si no lo tiene (Anexo hereda de StandardModelEstablishment)
                if nuevo_anexo.servicio:
                    nuevo_anexo.establecimiento = nuevo_anexo.servicio.establecimiento
            nuevo_anexo.updated_by = request.user
            nuevo_anexo.save()
            messages.success(request, "Anexo guardado correctamente")
            return redirect('agenda:editor')
        else:
            # Si hay error, podrías querer manejarlo de otra forma, pero por ahora redirección con error
            messages.error(request, "Error al guardar el anexo. Por favor revise los datos.")
            return redirect('agenda:editor')

    return redirect('agenda:editor')


@login_required
def editar_anexo_form(request, pk):
    perfil = getattr(request.user, 'perfilagenda', None)
    if not perfil or not perfil.editor:
        return HttpResponse(status=403)

    anexo = get_object_or_404(Anexo, pk=pk)
    if anexo.servicio not in perfil.servicio.all():
        return HttpResponse("No tiene permiso para editar este anexo", status=403)

    form = FormAnexo(instance=anexo, servicios_disponibles=perfil.servicio.filter(is_active=True))

    # Renderizamos solo la parte del formulario (o podrías cargar esto vía AJAX)
    # Para simplicidad inicial, haremos que 'editor' use este form si se pasa un pk

    establecimiento_id = request.GET.get('establecimiento')
    establecimiento = None
    if establecimiento_id:
        establecimiento = get_object_or_404(Establecimiento, id=establecimiento_id)

    form_filter = AnexoFilterForm(request.GET or None, establecimiento=establecimiento_id)
    form_filter.fields['servicio'].queryset = perfil.servicio.filter(is_active=True)

    return render(request, 'anexos/crud.html', {
        'form': form_filter,
        'form_anexo': form,
        'anexo_edit': anexo,
        'establecimiento_id': establecimiento_id,
        'establecimiento': establecimiento
    })


@login_required
def eliminar_anexo(request, pk):
    perfil = getattr(request.user, 'perfilagenda', None)
    if not perfil or not perfil.editor:
        return HttpResponse(status=403)

    anexo = get_object_or_404(Anexo, pk=pk)
    if anexo.servicio not in perfil.servicio.all():
        return HttpResponse("No tiene permiso para eliminar este anexo", status=403)

    anexo.delete()
    messages.success(request, "Anexo eliminado correctamente")
    return redirect('agenda:editor')


def buscar_anexo(request):
    q = request.GET.get("q", "").strip()
    servicio_id = request.GET.get("servicio")
    establecimiento_id = request.GET.get("establecimiento")
    per_page = request.GET.get("per_page", 10)
    page_number = request.GET.get("page", 1)

    queryset = Anexo.objects.all()

    if establecimiento_id:
        queryset = queryset.filter(servicio__establecimiento_id=establecimiento_id)

    if q:
        queryset = queryset.filter(
            Q(nombre__icontains=q) |
            Q(anexo__icontains=q) |
            Q(email__icontains=q)
        )

    if servicio_id:
        queryset = queryset.filter(servicio=servicio_id)

    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page_number)

    table_columns = [
        {'name': 'anexo', 'label': 'Anexo'},
        {'name': 'anexo_publico', 'label': 'Público'},
        {'name': 'nombre', 'label': 'Nombre'},
        {'name': 'servicio', 'label': 'Servicio'},
        {'name': 'email', 'label': 'Correo'},
    ]

    return render(
        request,
        'anexos/components/_table_result.html',
        {
            "object_list": page_obj,
            "table_columns": table_columns,
            "establecimiento_id": establecimiento_id,
        },
    )
