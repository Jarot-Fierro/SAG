from django.urls import path

from solicitud_vpn.views import (
    SolicitudVPNMisSolicitudesListView,
    SolicitudVPNCreateView,
    SolicitudVPNBandejaTICListView,
    SolicitudVPNDetalleView,
    SolicitudVPNCambiarEstadoView,
    PerfilVPNView,
    FuncionarioDataAPIView,
)

app_name = 'solicitud_vpn'

urlpatterns = [
    path('', SolicitudVPNMisSolicitudesListView.as_view(), name='mis_solicitudes'),
    path('crear/', SolicitudVPNCreateView.as_view(), name='crear'),
    path('bandeja-tic/', SolicitudVPNBandejaTICListView.as_view(), name='bandeja_tic'),
    path('detalle/<int:pk>/', SolicitudVPNDetalleView.as_view(), name='detalle'),
    path('cambiar-estado/<int:pk>/', SolicitudVPNCambiarEstadoView.as_view(), name='cambiar_estado'),
    path('perfil/', PerfilVPNView.as_view(), name='perfil'),
    path('api/funcionario/<int:pk>/', FuncionarioDataAPIView.as_view(), name='api_funcionario'),
]
