from .catalogos import (
    LugarDestinoListView, LugarDestinoCreateView, LugarDestinoUpdateView, LugarDestinoDetailView, lugar_destino_delete,
    EscalaViaticoListView, EscalaViaticoCreateView, EscalaViaticoUpdateView, EscalaViaticoDetailView,
    escala_viatico_delete,
    VistoLegalListView, VistoLegalCreateView, VistoLegalUpdateView, VistoLegalDetailView, visto_legal_delete
)
from .control_asistencia import (
    ValidacionRelojControlListView, ValidacionRelojControlCreateView, ValidacionRelojControlUpdateView,
    ValidacionRelojControlDetailView, validacion_reloj_delete, sincronizar_reloj_toggle,
    PermisoGremialListView, PermisoGremialCreateView, PermisoGremialUpdateView, PermisoGremialDetailView,
    permiso_gremial_delete
)
from .dashboard import ViaticosDashboardView
from .finanzas import (
    EgresoPagoViaticoListView, EgresoPagoViaticoCreateView, EgresoPagoViaticoUpdateView, EgresoPagoViaticoDetailView,
    egreso_pago_delete,
    RendicionCometidoListView, RendicionCometidoCreateView, RendicionCometidoUpdateView, RendicionCometidoDetailView,
    DetalleRendicionGastoCreateView, DetalleRendicionGastoUpdateView, detalle_rendicion_gasto_delete
)
from .resoluciones import (
    ResolucionCometidoListView, ResolucionCometidoCreateView, ResolucionCometidoUpdateView,
    ResolucionCometidoDetailView,
    resolucion_cometido_delete
)
from .solicitudes import (
    SolicitudListView, MisSolicitudesListView, SolicitudCreateView, SolicitudUpdateView, SolicitudDetailView,
    solicitud_delete, solicitud_enviar_jefatura, solicitud_anular,
    ItinerarioCreateView, ItinerarioUpdateView, itinerario_delete, CalculoViaticoUpdateView
)
from .transporte import (
    GastoTransporteListView, GastoTransporteCreateView, GastoTransporteUpdateView, GastoTransporteDetailView,
    gasto_transporte_delete
)
from .workflow import (
    BandejaFirmasListView, AprobacionCometidoCreateView, HistorialFirmasListView
)

__all__ = [
    # Catalogos
    'LugarDestinoListView', 'LugarDestinoCreateView', 'LugarDestinoUpdateView', 'LugarDestinoDetailView',
    'lugar_destino_delete',
    'EscalaViaticoListView', 'EscalaViaticoCreateView', 'EscalaViaticoUpdateView', 'EscalaViaticoDetailView',
    'escala_viatico_delete',
    'VistoLegalListView', 'VistoLegalCreateView', 'VistoLegalUpdateView', 'VistoLegalDetailView', 'visto_legal_delete',
    # Solicitudes
    'SolicitudListView', 'MisSolicitudesListView', 'SolicitudCreateView', 'SolicitudUpdateView', 'SolicitudDetailView',
    'solicitud_delete', 'solicitud_enviar_jefatura', 'solicitud_anular',
    'ItinerarioCreateView', 'ItinerarioUpdateView', 'itinerario_delete', 'CalculoViaticoUpdateView',
    # Transporte
    'GastoTransporteListView', 'GastoTransporteCreateView', 'GastoTransporteUpdateView', 'GastoTransporteDetailView',
    'gasto_transporte_delete',
    # Workflow
    'BandejaFirmasListView', 'AprobacionCometidoCreateView', 'HistorialFirmasListView',
    # Resoluciones
    'ResolucionCometidoListView', 'ResolucionCometidoCreateView', 'ResolucionCometidoUpdateView',
    'ResolucionCometidoDetailView',
    'resolucion_cometido_delete',
    # Finanzas
    'EgresoPagoViaticoListView', 'EgresoPagoViaticoCreateView', 'EgresoPagoViaticoUpdateView',
    'EgresoPagoViaticoDetailView',
    'egreso_pago_delete',
    'RendicionCometidoListView', 'RendicionCometidoCreateView', 'RendicionCometidoUpdateView',
    'RendicionCometidoDetailView',
    'DetalleRendicionGastoCreateView', 'DetalleRendicionGastoUpdateView', 'detalle_rendicion_gasto_delete',
    # Control Asistencia
    'ValidacionRelojControlListView', 'ValidacionRelojControlCreateView', 'ValidacionRelojControlUpdateView',
    'ValidacionRelojControlDetailView', 'validacion_reloj_delete', 'sincronizar_reloj_toggle',
    'PermisoGremialListView', 'PermisoGremialCreateView', 'PermisoGremialUpdateView', 'PermisoGremialDetailView',
    'permiso_gremial_delete',
    # Dashboard
    'ViaticosDashboardView',
]
