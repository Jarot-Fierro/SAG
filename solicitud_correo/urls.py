from django.urls import path

from solicitud_correo.views import (
    SolicitudMisSolicitudesListView,
    SolicitudCorreoCreateView,
    SolicitudCorreoDetailView,
    SolicitudBandejaRRHHListView,
    SolicitudRevisionRRHHView,
    SolicitudBandejaTICListView,
    SolicitudProcesamientoTICView,
    SolicitudHistorialView,
    detalle_revisar_rrhh,
    solicitud_aprobar_todos_rrhh,
    detalle_procesar_tic,
    detalle_notificar_funcionario,
    solicitud_cancelar,
    api_funcionario_info
)

app_name = 'solicitud_correo'

urlpatterns = [
    # Mis Solicitudes
    path('', SolicitudMisSolicitudesListView.as_view(), name='mis_solicitudes'),
    path('crear/', SolicitudCorreoCreateView.as_view(), name='crear'),
    path('detalle/<int:pk>/', SolicitudCorreoDetailView.as_view(), name='detalle'),
    path('cancelar/<int:pk>/', solicitud_cancelar, name='cancelar'),
    path('historial/<int:pk>/', SolicitudHistorialView.as_view(), name='historial'),

    # Bandeja y Revisión RR.HH.
    path('rrhh/bandeja/', SolicitudBandejaRRHHListView.as_view(), name='bandeja_rrhh'),
    path('rrhh/revision/<int:pk>/', SolicitudRevisionRRHHView.as_view(), name='revision_rrhh'),
    path('rrhh/revisar-detalle/<int:pk>/', detalle_revisar_rrhh, name='revisar_detalle_rrhh'),
    path('rrhh/aprobar-todos/<int:pk>/', solicitud_aprobar_todos_rrhh, name='aprobar_todos_rrhh'),

    # Bandeja y Procesamiento TIC
    path('tic/bandeja/', SolicitudBandejaTICListView.as_view(), name='bandeja_tic'),
    path('tic/procesamiento/<int:pk>/', SolicitudProcesamientoTICView.as_view(), name='procesamiento_tic'),
    path('tic/procesar-detalle/<int:pk>/', detalle_procesar_tic, name='procesar_detalle_tic'),

    # Notificación a Funcionario
    path('notificar-detalle/<int:pk>/', detalle_notificar_funcionario, name='notificar_detalle'),

    # API auxiliar
    path('api/funcionario/<int:pk>/', api_funcionario_info, name='api_funcionario_info'),
]
