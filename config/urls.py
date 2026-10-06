from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include

from config import settings
from core.models.funcionario import Funcionario


# def funcionarios_api(request):
#     q = request.GET.get("q", "")
#     pagina = request.GET.get("page", 1)
#
#     funcionarios = Funcionario.objects.all()
#
#     if q:
#         funcionarios = funcionarios.filter(
#             nombre__icontains=q
#         )
#
#     paginator = Paginator(funcionarios, 100)
#     pagina_obj = paginator.get_page(pagina)
#
#     datos = []
#
#     for funcionario in pagina_obj:
#         datos.append({
#             "id": funcionario.id,
#             "nombre": funcionario.nombre,
#             "rut": funcionario.rut,
#             "establecimiento": funcionario.establecimiento.nombre
#         })
#
#     respuesta = JsonResponse({
#         "funcionarios": datos,
#         "pagina": pagina_obj.number,
#         "total_paginas": paginator.num_pages,
#         "total": paginator.count,
#     })
#
#     respuesta["Access-Control-Allow-Origin"] = "*"
#
#     return respuesta


def funcionarios_api(request):

    # Parámetros enviados por DataTables
    draw = int(request.GET.get("draw", 1))
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))

    # Texto buscado
    busqueda = request.GET.get("search[value]", "")

    # Parámetros de ordenamiento
    order_column = request.GET.get("order[0][column]", "0")
    order_direction = request.GET.get("order[0][dir]", "asc")

    # Queryset base
    funcionarios = Funcionario.objects.all()

    # Total antes de buscar
    total = funcionarios.count()

    # Aplicar búsqueda
    if busqueda:
        funcionarios = funcionarios.filter(
            nombre__icontains=busqueda
        )

    # Total después de buscar
    total_filtrado = funcionarios.count()

    # Columnas que DataTables puede ordenar
    columnas = {
        "0": "id",
        "1": "nombre",
        "2": "rut",
        "3": "establecimiento__nombre",
    }

    # Obtener columna
    campo = columnas.get(
        order_column,
        "id"
    )

    # Aplicar dirección
    if order_direction == "desc":
        campo = f"-{campo}"

    # Ordenar
    funcionarios = funcionarios.order_by(campo)

    # Paginación
    funcionarios = funcionarios[start:start + length]

    datos = []

    for funcionario in funcionarios:

        datos.append({
            "id": funcionario.id,
            "nombre": funcionario.nombre,
            "rut": funcionario.rut,
            "establecimiento": (
                funcionario.establecimiento.nombre
                if funcionario.establecimiento
                else ""
            ),
        })

    respuesta = JsonResponse({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": total_filtrado,
        "data": datos,
    })

    respuesta["Access-Control-Allow-Origin"] = "*"

    return respuesta
urlpatterns = [
    path('admin/', admin.site.urls),
    path("select2/", include("django_select2.urls")),
    path('', include('core.urls')),
    path('agenda/', include('agenda_telefonica.urls')),
    path('soporte/', include('soporte.urls')),
    path('horos/', include('horos.urls')),
    path('gestion/', include('gestion_tic.urls')),
    path('bodega/', include('bodega.urls')),
    path('solicitudes-correo/', include('solicitud_correo.urls')),
    path('solicitudes-vpn/', include('solicitud_vpn.urls')),
    path('api/funcionarios/', funcionarios_api),
]

handler404 = 'core.views.errors.handler404'
handler403 = 'core.views.errors.handler403'
handler500 = 'core.views.errors.handler500'

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
