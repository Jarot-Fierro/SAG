from django.urls import path

from .views import (
    # Dashboard
    ViaticosDashboardView,
    # Solicitudes
    SolicitudListView, MisSolicitudesListView, SolicitudCreateView, SolicitudUpdateView, SolicitudDetailView,
    solicitud_delete, solicitud_enviar_jefatura, solicitud_anular,
    ItinerarioCreateView, ItinerarioUpdateView, itinerario_delete, CalculoViaticoUpdateView,
    # Transporte
    GastoTransporteListView, GastoTransporteCreateView, GastoTransporteUpdateView, GastoTransporteDetailView,
    gasto_transporte_delete,
    # Workflow
    BandejaFirmasListView, AprobacionCometidoCreateView, HistorialFirmasListView,
    # Resoluciones
    ResolucionCometidoListView, ResolucionCometidoCreateView, ResolucionCometidoUpdateView,
    ResolucionCometidoDetailView,
    resolucion_cometido_delete,
    # Finanzas
    EgresoPagoViaticoListView, EgresoPagoViaticoCreateView, EgresoPagoViaticoUpdateView, EgresoPagoViaticoDetailView,
    egreso_pago_delete,
    RendicionCometidoListView, RendicionCometidoCreateView, RendicionCometidoUpdateView, RendicionCometidoDetailView,
    DetalleRendicionGastoCreateView, DetalleRendicionGastoUpdateView, detalle_rendicion_gasto_delete,
    # Asistencia
    ValidacionRelojControlListView, ValidacionRelojControlCreateView, ValidacionRelojControlUpdateView,
    ValidacionRelojControlDetailView, validacion_reloj_delete, sincronizar_reloj_toggle,
    PermisoGremialListView, PermisoGremialCreateView, PermisoGremialUpdateView, PermisoGremialDetailView,
    permiso_gremial_delete,
    # Catalogos
    LugarDestinoListView, LugarDestinoCreateView, LugarDestinoUpdateView, LugarDestinoDetailView, lugar_destino_delete,
    EscalaViaticoListView, EscalaViaticoCreateView, EscalaViaticoUpdateView, EscalaViaticoDetailView,
    escala_viatico_delete,
    VistoLegalListView, VistoLegalCreateView, VistoLegalUpdateView, VistoLegalDetailView, visto_legal_delete,
)

app_name = 'viaticos'

urlpatterns = [
    # Dashboard
    path('', ViaticosDashboardView.as_view(), name='dashboard'),

    # Solicitudes
    path('solicitudes/', SolicitudListView.as_view(), name='solicitud_list'),
    path('solicitudes/mis-solicitudes/', MisSolicitudesListView.as_view(), name='mis_solicitudes_list'),
    path('solicitudes/crear/', SolicitudCreateView.as_view(), name='solicitud_create'),
    path('solicitudes/<int:pk>/', SolicitudDetailView.as_view(), name='solicitud_detail'),
    path('solicitudes/<int:pk>/editar/', SolicitudUpdateView.as_view(), name='solicitud_update'),
    path('solicitudes/<int:pk>/desactivar/', solicitud_delete, name='solicitud_delete'),
    path('solicitudes/<int:pk>/enviar-jefatura/', solicitud_enviar_jefatura, name='solicitud_enviar_jefatura'),
    path('solicitudes/<int:pk>/anular/', solicitud_anular, name='solicitud_anular'),

    # Itinerarios
    path('solicitudes/<int:solicitud_id>/itinerario/crear/', ItinerarioCreateView.as_view(), name='itinerario_create'),
    path('itinerario/<int:pk>/editar/', ItinerarioUpdateView.as_view(), name='itinerario_update'),
    path('itinerario/<int:pk>/eliminar/', itinerario_delete, name='itinerario_delete'),

    # Cálculo Financiero
    path('calculo/<int:pk>/editar/', CalculoViaticoUpdateView.as_view(), name='calculo_update'),

    # Transporte
    path('transporte/', GastoTransporteListView.as_view(), name='transporte_list'),
    path('transporte/crear/', GastoTransporteCreateView.as_view(), name='transporte_create'),
    path('transporte/<int:pk>/editar/', GastoTransporteUpdateView.as_view(), name='transporte_update'),
    path('transporte/<int:pk>/detalle/', GastoTransporteDetailView.as_view(), name='transporte_detail'),
    path('transporte/<int:pk>/desactivar/', gasto_transporte_delete, name='transporte_delete'),

    # Workflow & Firmas
    path('workflow/bandeja/', BandejaFirmasListView.as_view(), name='bandeja_firmas'),
    path('workflow/<int:solicitud_id>/aprobar/', AprobacionCometidoCreateView.as_view(), name='aprobacion_create'),
    path('workflow/historial/', HistorialFirmasListView.as_view(), name='historial_firmas'),

    # Resoluciones
    path('resoluciones/', ResolucionCometidoListView.as_view(), name='resolucion_list'),
    path('resoluciones/crear/', ResolucionCometidoCreateView.as_view(), name='resolucion_create'),
    path('resoluciones/<int:pk>/editar/', ResolucionCometidoUpdateView.as_view(), name='resolucion_update'),
    path('resoluciones/<int:pk>/detalle/', ResolucionCometidoDetailView.as_view(), name='resolucion_detail'),
    path('resoluciones/<int:pk>/desactivar/', resolucion_cometido_delete, name='resolucion_delete'),

    # Finanzas - Egresos
    path('finanzas/egresos/', EgresoPagoViaticoListView.as_view(), name='egreso_list'),
    path('finanzas/egresos/crear/', EgresoPagoViaticoCreateView.as_view(), name='egreso_create'),
    path('finanzas/egresos/<int:pk>/editar/', EgresoPagoViaticoUpdateView.as_view(), name='egreso_update'),
    path('finanzas/egresos/<int:pk>/detalle/', EgresoPagoViaticoDetailView.as_view(), name='egreso_detail'),
    path('finanzas/egresos/<int:pk>/desactivar/', egreso_pago_delete, name='egreso_delete'),

    # Finanzas - Rendiciones
    path('finanzas/rendiciones/', RendicionCometidoListView.as_view(), name='rendicion_list'),
    path('finanzas/rendiciones/crear/', RendicionCometidoCreateView.as_view(), name='rendicion_create'),
    path('finanzas/rendiciones/<int:pk>/editar/', RendicionCometidoUpdateView.as_view(), name='rendicion_update'),
    path('finanzas/rendiciones/<int:pk>/detalle/', RendicionCometidoDetailView.as_view(), name='rendicion_detail'),

    # Finanzas - Detalle Gastos Rendidos
    path('finanzas/rendiciones/<int:rendicion_id>/detalle-gasto/crear/', DetalleRendicionGastoCreateView.as_view(),
         name='detalle_gasto_create'),
    path('finanzas/detalle-gasto/<int:pk>/editar/', DetalleRendicionGastoUpdateView.as_view(),
         name='detalle_gasto_update'),
    path('finanzas/detalle-gasto/<int:pk>/eliminar/', detalle_rendicion_gasto_delete, name='detalle_gasto_delete'),

    # Asistencia - Reloj Control
    path('asistencia/reloj/', ValidacionRelojControlListView.as_view(), name='reloj_list'),
    path('asistencia/reloj/crear/', ValidacionRelojControlCreateView.as_view(), name='reloj_create'),
    path('asistencia/reloj/<int:pk>/editar/', ValidacionRelojControlUpdateView.as_view(), name='reloj_update'),
    path('asistencia/reloj/<int:pk>/detalle/', ValidacionRelojControlDetailView.as_view(), name='reloj_detail'),
    path('asistencia/reloj/<int:pk>/desactivar/', validacion_reloj_delete, name='reloj_delete'),
    path('asistencia/reloj/<int:pk>/toggle-sync/', sincronizar_reloj_toggle, name='reloj_toggle_sync'),

    # Asistencia - Permisos Gremiales
    path('asistencia/permisos-gremiales/', PermisoGremialListView.as_view(), name='permiso_gremial_list'),
    path('asistencia/permisos-gremiales/crear/', PermisoGremialCreateView.as_view(), name='permiso_gremial_create'),
    path('asistencia/permisos-gremiales/<int:pk>/editar/', PermisoGremialUpdateView.as_view(),
         name='permiso_gremial_update'),
    path('asistencia/permisos-gremiales/<int:pk>/detalle/', PermisoGremialDetailView.as_view(),
         name='permiso_gremial_detail'),
    path('asistencia/permisos-gremiales/<int:pk>/desactivar/', permiso_gremial_delete, name='permiso_gremial_delete'),

    # Catálogos - Lugares
    path('catalogos/lugares/', LugarDestinoListView.as_view(), name='lugar_list'),
    path('catalogos/lugares/crear/', LugarDestinoCreateView.as_view(), name='lugar_create'),
    path('catalogos/lugares/<int:pk>/editar/', LugarDestinoUpdateView.as_view(), name='lugar_update'),
    path('catalogos/lugares/<int:pk>/detalle/', LugarDestinoDetailView.as_view(), name='lugar_detail'),
    path('catalogos/lugares/<int:pk>/desactivar/', lugar_destino_delete, name='lugar_delete'),

    # Catálogos - Escalas
    path('catalogos/escalas/', EscalaViaticoListView.as_view(), name='escala_list'),
    path('catalogos/escalas/crear/', EscalaViaticoCreateView.as_view(), name='escala_create'),
    path('catalogos/escalas/<int:pk>/editar/', EscalaViaticoUpdateView.as_view(), name='escala_update'),
    path('catalogos/escalas/<int:pk>/detalle/', EscalaViaticoDetailView.as_view(), name='escala_detail'),
    path('catalogos/escalas/<int:pk>/desactivar/', escala_viatico_delete, name='escala_delete'),

    # Catálogos - Vistos Legales
    path('catalogos/vistos/', VistoLegalListView.as_view(), name='visto_list'),
    path('catalogos/vistos/crear/', VistoLegalCreateView.as_view(), name='visto_create'),
    path('catalogos/vistos/<int:pk>/editar/', VistoLegalUpdateView.as_view(), name='visto_update'),
    path('catalogos/vistos/<int:pk>/detalle/', VistoLegalDetailView.as_view(), name='visto_detail'),
    path('catalogos/vistos/<int:pk>/desactivar/', visto_legal_delete, name='visto_delete'),
]
