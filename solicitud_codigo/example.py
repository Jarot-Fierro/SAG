# Create your views here.
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic import ListView

from agenda_telefonica.models import Anexo
from core.models.unidad_organizacional import UnidadOrganizacional


class AnexoListCBV(ListView):
    model = Anexo
    template_name = "anexos/index.html"
    context_object_name = "anexos"

    view_title = "Anexos"
    view_type = "CBV"

    columns = [
        "anexo",
        "anexo_publico",
        "numero_telefonico",
        "funcionario__nombre",
        "funcionario__email",
        "unidad_organizacional__nombre",
        "unidad_organizacional__direccion__nombre",
        "funcionario__rol_organizacional__nombre",
        "funcionario__cargo",
    ]

    searchable_columns = columns

    def get_queryset(self):
        return (
            Anexo.objects
            .select_related(
                "funcionario__rol_organizacional",
                "funcionario__unidad_organizacional",
                "unidad_organizacional__direccion",
            )
            .filter(establecimiento=2)
        )

    def get_column_control_options(self):
        unidades = (
            UnidadOrganizacional.objects
            .filter(is_active=True)
            .values_list("nombre", flat=True)
            .distinct()
            .order_by("nombre")
        )

        return {
            "unidad_organizacional__nombre": [
                {"label": nombre, "value": nombre}
                for nombre in unidades
                if nombre
            ]
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_title"] = self.view_title
        context["view_type"] = self.view_type
        context["column_control_options"] = (
            self.get_column_control_options()
        )
        return context

    def get(self, request, *args, **kwargs):
        # Si DataTables solicita datos mediante AJAX,
        # devolvemos JSON en lugar de renderizar la plantilla.
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return self.datatables_response(request)

        return super().get(request, *args, **kwargs)

    def datatables_response(self, request):
        queryset = self.get_queryset()

        draw = int(request.GET.get("draw", 1))
        start = max(int(request.GET.get("start", 0)), 0)
        length = int(request.GET.get("length", 10))

        # Total de registros sin filtros.
        records_total = queryset.count()

        # Búsqueda global.
        search_value = request.GET.get("search[value]", "").strip()

        if search_value:
            search_query = Q()

            for column in self.searchable_columns:
                search_query |= Q(
                    **{f"{column}__icontains": search_value}
                )

            queryset = queryset.filter(search_query)

        # Filtro de columna para la unidad organizacional.
        unidad_filter = request.GET.get("columns[5][search][value]", "").strip()

        if unidad_filter:
            queryset = queryset.filter(
                unidad_organizacional__nombre__icontains=unidad_filter
            )

        # Total después de aplicar los filtros.
        records_filtered = queryset.count()

        # Ordenamiento solicitado por DataTables.
        order_column = request.GET.get("order[0][column]")
        order_dir = request.GET.get("order[0][dir]", "asc")

        if order_column is not None:
            try:
                column_index = int(order_column)

                if 0 <= column_index < len(self.columns):
                    field = self.columns[column_index]

                    if order_dir == "desc":
                        field = f"-{field}"

                    queryset = queryset.order_by(field)
            except (ValueError, TypeError):
                pass

        # Paginación.
        if length != -1:
            queryset = queryset[start:start + min(length, 500)]

        data = [
            self.serialize_anexo(anexo)
            for anexo in queryset
        ]

        return JsonResponse({
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data,
        })

    @staticmethod
    def serialize_anexo(anexo):
        funcionario = anexo.funcionario
        unidad = anexo.unidad_organizacional

        # NOMBRE DEL FUNCIONARIO
        if funcionario and funcionario.nombre:
            funcionario__nombre = funcionario.nombre
        elif anexo.nombre_anexo:
            funcionario__nombre = anexo.nombre_anexo
        else:
            funcionario__nombre = ""

        # EMAIL DEL FUNCIONARIO
        if funcionario and funcionario.email:
            funcionario__email = funcionario.email
        elif anexo.email:
            funcionario__email = anexo.email
        else:
            funcionario__email = ""

        # UNIDAD ORGANIZACIONAL
        if unidad and unidad.nombre:
            unidad_organizacional__nombre = unidad.nombre
        elif anexo.unidad_organizacional and anexo.unidad_organizacional.nombre:
            unidad_organizacional__nombre = anexo.unidad_organizacional.nombre
        else:
            unidad_organizacional__nombre = ""

        # DIRECCIÓN DE LA UNIDAD ORGANIZACIONAL
        if unidad and unidad.direccion and unidad.direccion.nombre:
            unidad_organizacional__direccion__nombre = unidad.direccion.nombre
        elif (
                anexo.unidad_organizacional
                and anexo.unidad_organizacional.direccion
                and anexo.unidad_organizacional.direccion.nombre
        ):
            unidad_organizacional__direccion__nombre = (
                anexo.unidad_organizacional.direccion.nombre
            )
        else:
            unidad_organizacional__direccion__nombre = ""

        # ROL ORGANIZACIONAL
        if funcionario and funcionario.rol_organizacional and funcionario.rol_organizacional.nombre:
            funcionario__rol_organizacional__nombre = funcionario.rol_organizacional.nombre
        elif anexo.rol_organizacional and anexo.rol_organizacional.nombre:
            funcionario__rol_organizacional__nombre = anexo.rol_organizacional.nombre
        else:
            funcionario__rol_organizacional__nombre = ""

        # CARGO DEL FUNCIONARIO
        if funcionario and funcionario.cargo:
            funcionario__cargo = funcionario.cargo
        elif anexo.encargado_de:
            funcionario__cargo = anexo.encargado_de
        else:
            funcionario__cargo = ""

        # LINK GOOGLE MAPS
        if funcionario and funcionario.unidad_organizacional.direccion.enlace_google_maps:
            unidad_organizacional__direccion__enlace_google_maps = funcionario.unidad_organizacional.direccion.enlace_google_maps
        elif anexo.unidad_organizacional.direccion.enlace_google_maps:
            unidad_organizacional__direccion__enlace_google_maps = anexo.unidad_organizacional.direccion.enlace_google_maps
        else:
            unidad_organizacional__direccion__enlace_google_maps = ""

        return {
            "anexo": anexo.anexo,
            "anexo_publico": anexo.anexo_publico,
            "numero_telefonico": anexo.numero_telefonico,
            "funcionario__nombre": funcionario__nombre,
            "funcionario__email": funcionario__email,
            "unidad_organizacional__nombre": unidad_organizacional__nombre,
            "unidad_organizacional__direccion__nombre": unidad_organizacional__direccion__nombre,
            "funcionario__rol_organizacional__nombre": funcionario__rol_organizacional__nombre,
            "funcionario__cargo": funcionario__cargo,
            "unidad_organizacional__direccion__enlace_google_maps": unidad_organizacional__direccion__enlace_google_maps,
        }
