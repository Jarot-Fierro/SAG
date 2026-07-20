from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView

from core.filters.funcionarios import FuncionarioFilter
from core.forms.funcionarios import FuncionarioForm
from core.models.funcionario import Funcionario


def funcionario_api_view(request):
    term = request.GET.get("term", "")
    if not term:
        return JsonResponse({"error": "No term provided"}, status=400)

    # Buscar por id, rut, nombres, apellidos o correo
    # Generalmente se consultará por rut
    queryset = Funcionario.objects.filter(
        Q(id__iexact=term) |
        Q(rut__iexact=term) |
        Q(nombres__icontains=term) |
        Q(apellidos__icontains=term) |
        Q(email__icontains=term)
    ).select_related("profesion", "rol_organizacional", "unidad_organizacional")

    # Si hay más de uno, podrías devolver el primero o una lista. 
    # El requerimiento dice "devolver al funcionario", asumimos el más exacto o el primero.
    funcionario = queryset.first()

    if not funcionario:
        return JsonResponse({"not_found": True}, status=200)

    # Verificar si tiene anexo
    has_anexo = hasattr(funcionario, "anexo")
    anexo_info = None
    if has_anexo:
        anexo_info = {
            "anexo": funcionario.anexo.anexo,
            "unidad": funcionario.anexo.unidad_organizacional.nombre if funcionario.anexo.unidad_organizacional else "-"
        }

    data = {
        "id": funcionario.id,
        "rut": funcionario.rut,
        "nombres": funcionario.nombres,
        "apellidos": funcionario.apellidos,
        "email": funcionario.email,
        "cargo": funcionario.cargo,
        "profesion": funcionario.profesion_id,
        "rol_organizacional": funcionario.rol_organizacional_id,
        "unidad_organizacional": funcionario.unidad_organizacional_id,
        "has_anexo": has_anexo,
        "anexo_info": anexo_info
    }

    return JsonResponse(data)


class FuncionarioListView(ListView):
    model = Funcionario
    template_name = "funcionarios/list_funcionarios.html"
    context_object_name = "funcionarios"
    paginate_by = 10

    def get_queryset(self):
        establecimiento = self.request.user.establecimiento
        queryset = (
            super()
            .get_queryset()
            .filter(establecimiento=establecimiento)
            .select_related(
                "establecimiento",
                "profesion",
                "rol_organizacional",
                "unidad_organizacional",
            )
        )

        self.filter_form = FuncionarioFilter(self.request.GET)

        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data

            if data["rut"]:
                queryset = queryset.filter(rut__icontains=data["rut"])

            if data["nombres"]:
                queryset = queryset.filter(nombres__icontains=data["nombres"])

            if data["apellidos"]:
                queryset = queryset.filter(apellidos__icontains=data["apellidos"])

            if data["email"]:
                queryset = queryset.filter(email__icontains=data["email"])

            if data["rol_organizacional"]:
                queryset = queryset.filter(
                    rol_organizacional=data["rol_organizacional"]
                )

            if data["unidad_organizacional"]:
                queryset = queryset.filter(
                    unidad_organizacional=data["unidad_organizacional"]
                )

            if data["is_active"] != "":
                queryset = queryset.filter(
                    is_active=data["is_active"] == "True"
                )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        return context


class FuncionarioBaseFormView:
    model = Funcionario
    form_class = FuncionarioForm
    template_name = "funcionarios/form_funcionarios.html"
    success_url = reverse_lazy("funcionarios:list_funcionarios")
    page_title = "Formulario Funcionario"
    submit_label = "Guardar"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["submit_label"] = self.submit_label
        return context


class FuncionarioCreateView(FuncionarioBaseFormView, CreateView):
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

        form.instance.establecimiento = establecimiento
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Funcionario creado correctamente.")
        return super().form_valid(form)


class FuncionarioUpdateView(FuncionarioBaseFormView, UpdateView):
    page_title = "Editar funcionario"
    submit_label = "Actualizar"

    def form_valid(self, form):
        establecimiento = getattr(self.request.user, "establecimiento", None)
        if establecimiento:
            form.instance.establecimiento = establecimiento

        form.instance.updated_by = self.request.user
        messages.success(self.request, "Funcionario actualizado correctamente.")
        return super().form_valid(form)


@require_POST
def funcionario_delete_view(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk)
    funcionario.is_active = False
    funcionario.save()
    messages.success(request, "Funcionario eliminado correctamente.")
    return redirect("funcionarios:list_funcionarios")
