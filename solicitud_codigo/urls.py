from django.urls import path

from solicitud_codigo.views import (
    MisSolicitudesListView,
    BandejaReferenteListView,
    BandejaPendientesCreacionListView,
    SolicitudCreateView,
    SolicitudDetailView,
    SolicitudCorregirView,
    SolicitudObservarView,
    SolicitudRechazarView,
    SolicitudValidarView,
    SolicitudCrearCodigoView,
    SubareasPorAreaAPIView,
    BuscarCoincidenciasAPIView,
)

app_name = "solicitud_codigo"

urlpatterns = [
    # Bandeja del solicitante
    path("", MisSolicitudesListView.as_view(), name="mis_solicitudes"),
    path("mis-solicitudes/", MisSolicitudesListView.as_view(), name="mis_solicitudes_alias"),
    path("crear/", SolicitudCreateView.as_view(), name="crear"),

    # Detalle y corrección
    path("<int:pk>/detalle/", SolicitudDetailView.as_view(), name="detalle"),
    path("<int:pk>/corregir/", SolicitudCorregirView.as_view(), name="corregir"),

    # Bandeja del referente global y acciones
    path("referente/bandeja/", BandejaReferenteListView.as_view(), name="bandeja_referente"),
    path("<int:pk>/observar/", SolicitudObservarView.as_view(), name="observar"),
    path("<int:pk>/rechazar/", SolicitudRechazarView.as_view(), name="rechazar"),
    path("<int:pk>/validar/", SolicitudValidarView.as_view(), name="validar"),

    # Bandeja de creación efectiva y asignación de código
    path("creacion/bandeja/", BandejaPendientesCreacionListView.as_view(), name="bandeja_creacion"),
    path("<int:pk>/crear-codigo/", SolicitudCrearCodigoView.as_view(), name="crear_codigo"),

    # Endpoints auxiliares AJAX
    path("api/subareas/", SubareasPorAreaAPIView.as_view(), name="api_subareas"),
    path("api/buscar-coincidencias/", BuscarCoincidenciasAPIView.as_view(), name="api_coincidencias"),
]
