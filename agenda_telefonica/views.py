from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from agenda_telefonica.forms import AnexoFuncionarioForm
from agenda_telefonica.models import Anexo
from core.models.funcionario import Funcionario


def anexos_view(request, pk=None):
    if pk:
        anexo_instance = get_object_or_404(Anexo, pk=pk)
    else:
        anexo_instance = None

    if request.method == 'POST':
        form = AnexoFuncionarioForm(request.POST, instance=anexo_instance)
        if form.is_valid():
            rut = form.cleaned_data.get('rut').upper()
            nombres = form.cleaned_data.get('nombres').upper()
            apellidos = form.cleaned_data.get('apellidos').upper()
            email = form.cleaned_data.get('email')
            establecimiento = form.cleaned_data.get('establecimiento')
            cargo = form.cleaned_data.get('cargo')
            profesion = form.cleaned_data.get('profesion')

            # Buscar o crear/actualizar funcionario
            funcionario, created = Funcionario.objects.update_or_create(
                rut=rut,
                defaults={
                    'nombres': nombres,
                    'apellidos': apellidos,
                    'email': email,
                    'nombre': f"{nombres} {apellidos}",
                    'establecimiento': establecimiento,
                    'cargo': cargo,
                    'profesion': profesion,
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
        form = AnexoFuncionarioForm(instance=anexo_instance)

    anexos = Anexo.objects.filter(is_active=True)

    return render(request, 'anexos/anexos_form.html', {
        'form': form,
        'anexos': anexos,
        'is_edit': pk is not None
    })


def eliminar_anexo(request, pk):
    anexo = get_object_or_404(Anexo, pk=pk)
    anexo.is_active = False
    anexo.save()
    messages.info(request, "Anexo desactivado correctamente.")
    return redirect('agenda:anexos')
