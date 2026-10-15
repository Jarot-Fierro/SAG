from django.db.models import Q
from django.http import JsonResponse
from django.utils.text import Truncator
from django.views.generic import ListView

from soporte.models import Ticket


class SoporteListCBV(ListView):
    model = Ticket
    template_name = "tickets/list_v2.html"
    context_object_name = "anexos"

    view_title = "Soporte V2"
    view_type = "CBV"

    columns = [
        "numero_ticket",
        "titulo",
        "nombres",
        "estado",
        "area_soporte__nombre",
        "asignado_a__usuario__username",
        "fecha_cierre",
        "created_at",
    ]

    searchable_columns = [
        "numero_ticket",
        "titulo",
        "nombres",
        "estado",
        "area_soporte__nombre",
        "asignado_a__usuario__first_name",
        "asignado_a__usuario__last_name",
        "asignado_a__usuario__username",
    ]

    def get_queryset(self):
        try:
            areas_usuario = self.request.user.perfil_soporte.area_soporte.all()
            if (
                    hasattr(self.request.user, "establecimiento")
                    and self.request.user.establecimiento
                    and not self.request.user.is_superuser
            ):
                areas_usuario = areas_usuario.filter(establecimiento=self.request.user.establecimiento)

            queryset = super().get_queryset().select_related(
                "establecimiento", "area_soporte", "funcionario", "asignado_a", "asignado_a__usuario"
            ).filter(
                area_soporte__in=areas_usuario, is_active=True
            )

            if (
                    hasattr(self.request.user, "establecimiento")
                    and self.request.user.establecimiento
                    and not self.request.user.is_superuser
            ):
                queryset = queryset.filter(establecimiento=self.request.user.establecimiento)
        except AttributeError:
            # Si el usuario no tiene perfil_soporte, no ve ningún ticket
            queryset = super().get_queryset().none()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_title"] = self.view_title
        context["view_type"] = self.view_type
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
            self.serialize_ticket(ticket)
            for ticket in queryset
        ]

        return JsonResponse({
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data,
        })

    @staticmethod
    def serialize_ticket(ticket):
        return {
            "id": ticket.pk,
            "numero_ticket": ticket.numero_ticket,
            "titulo": Truncator(ticket.titulo).chars(30),
            "nombres": ticket.nombres,
            "estado": ticket.estado,
            "area_soporte": str(ticket.area_soporte.nombre) if ticket.area_soporte else None,
            "asignado_a": str(ticket.asignado_a) if ticket.asignado_a else None,
            "fecha_cierre": ticket.fecha_cierre.isoformat() if ticket.fecha_cierre else None,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        }