from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from gestion_tic.forms.campos_tipo_activos import CamposTipoActivos, CampoTipoActivoFormSet
from gestion_tic.forms.tipo_activo import FormTipoActivo
from gestion_tic.models.tipo_activo import TipoActivo


def campos_tipo_activos(request):
    # Obtener todos los TipoActivo del establecimiento para el selector
    list_tipo_activos = TipoActivo.objects.filter(establecimiento=request.user.establecimiento).order_by('nombre')

    # Determinar el TipoActivo actual
    tipo_id = request.GET.get('tipo')
    if tipo_id:
        tipo_activo = get_object_or_404(TipoActivo, id=tipo_id, establecimiento=request.user.establecimiento)
    else:
        tipo_activo = list_tipo_activos.first()

    if not tipo_activo:
        # Si no hay tipos de activo, podrías redirigir o mostrar un mensaje
        return render(request, 'gestion_tic/activos/form_campos_tipo_activos.html', {
            'title': 'Gestión de Campos por Tipo de Activo',
            'error': 'No existen tipos de activo creados.'
        })

    if request.method == 'POST':
        form_tipo = FormTipoActivo(request.POST, instance=tipo_activo)
        formset = CampoTipoActivoFormSet(request.POST, instance=tipo_activo, prefix='campos')

        if form_tipo.is_valid() and formset.is_valid():
            form_tipo.save()
            formset.save()
            messages.success(request, "Configuración guardada correctamente.")
            return redirect(f"{request.path}?tipo={tipo_activo.id}")
    else:
        form_tipo = FormTipoActivo(instance=tipo_activo)
        formset = CampoTipoActivoFormSet(instance=tipo_activo, prefix='campos')

    # Formulario de selección inicializado con el activo actual
    form_seleccion = CamposTipoActivos(initial={'tipo_activo': tipo_activo})
    # Filtrar el queryset del selector para que solo muestre los del establecimiento
    form_seleccion.fields['tipo_activo'].queryset = list_tipo_activos

    return render(request, 'gestion_tic/activos/form_campos_tipo_activos.html', {
        'tipo_activo': tipo_activo,
        'form_tipo': form_tipo,
        'formset': formset,
        'form_seleccion': form_seleccion,
        'title': f'Campos de {tipo_activo.nombre}',
    })
