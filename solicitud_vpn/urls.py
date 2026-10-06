from django.urls import path

from solicitud_vpn.views import (
    SolicitudVPNMisSolicitudesListView,
    SolicitudVPNCreateView,
    SolicitudVPNBandejaTICListView,
    SolicitudVPNDetalleView,
    SolicitudVPNCambiarEstadoView,
    PerfilVPNView,
    FuncionarioDataAPIView,
    solicitud_marcar_econecta,
    solicitud_marcar_completado,
    solicitud_eliminar,
    solicitud_notificar_solicitante,
)

app_name = 'solicitud_vpn'

urlpatterns = [
    path('', SolicitudVPNMisSolicitudesListView.as_view(), name='mis_solicitudes'),
    path('crear/', SolicitudVPNCreateView.as_view(), name='crear'),
    path('bandeja-tic/', SolicitudVPNBandejaTICListView.as_view(), name='bandeja_tic'),
    path('detalle/<int:pk>/', SolicitudVPNDetalleView.as_view(), name='detalle'),
    path('cambiar-estado/<int:pk>/', SolicitudVPNCambiarEstadoView.as_view(), name='cambiar_estado'),
    path('marcar-econecta/<int:pk>/', solicitud_marcar_econecta, name='marcar_econecta'),
    path('marcar-completado/<int:pk>/', solicitud_marcar_completado, name='marcar_completado'),
    path('eliminar/<int:pk>/', solicitud_eliminar, name='eliminar'),
    path('notificar/<int:pk>/', solicitud_notificar_solicitante, name='notificar'),
    path('perfil/', PerfilVPNView.as_view(), name='perfil'),
    path('api/funcionario/<int:pk>/', FuncionarioDataAPIView.as_view(), name='api_funcionario'),
]
