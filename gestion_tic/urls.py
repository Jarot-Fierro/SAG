from django.urls import path

from .views import catalogo, tipo_activo, campos_tipo_activos, activos, movimientos_activo, pdfs, equipos_baja
from .views import opciones_campo_tipo_activo, dashboard_gestion_tic

app_name = 'gestion_tic'

urlpatterns = [

    path('', dashboard_gestion_tic.DashboardGestionTicView.as_view(), name='dashboard_gestion_tic'),

    path('activo/acta/pdf/<int:pk>/', pdfs.generar_acta_activo, name='activo_acta_pdf'),
    path('activo/acta-personalizada/pdf/', pdfs.generar_acta_activo_personalizada,
         name='generar_acta_activo_personalizada'),

    # Activos
    path('activo/', activos.ActivoListView.as_view(), name='activo_list'),
    path('activo/crear/', activos.ActivoCreateView.as_view(), name='activo_create'),
    path('activo/<int:pk>/editar/', activos.ActivoUpdateView.as_view(), name='activo_update'),
    path('activo/<int:pk>/desactivar/', activos.activo_desactivar, name='activo_deactivate'),
    path('activos/', activos.ActivoListView.as_view()),
    path('activos/nuevo/', activos.ActivoCreateView.as_view()),
    path('activos/editar/<int:pk>/', activos.ActivoUpdateView.as_view(), name='activo_edit'),
    path('activo/desactivar/<int:pk>/', activos.activo_desactivar, name='activo_delete'),

    # Marca
    path('catalogo/marca/', catalogo.MarcaListView.as_view(), name='marca_list'),
    path('catalogo/marca/crear/', catalogo.MarcaCreateView.as_view(), name='marca_create'),
    path('catalogo/marca/<int:pk>/editar/', catalogo.MarcaUpdateView.as_view(), name='marca_update'),
    path('catalogo/marca/<int:pk>/desactivar/', catalogo.marca_desactivar, name='marca_deactivate'),
    path('catalogo/marca/nuevo/', catalogo.MarcaCreateView.as_view()),
    path('catalogo/marca/editar/<int:pk>/', catalogo.MarcaUpdateView.as_view()),
    path('catalogo/marca/desactivar/<int:pk>/', catalogo.marca_desactivar, name='marca_delete'),

    # Ips
    path('catalogo/ips/', catalogo.IpsListView.as_view(), name='ips_list'),
    path('catalogo/ips/crear/', catalogo.IpsCreateView.as_view(), name='ips_create'),
    path('catalogo/ips/<int:pk>/editar/', catalogo.IpsUpdateView.as_view(), name='ips_update'),
    path('catalogo/ips/<int:pk>/desactivar/', catalogo.ips_desactivar, name='ips_deactivate'),
    path('catalogo/ips/nuevo/', catalogo.IpsCreateView.as_view()),
    path('catalogo/ips/editar/<int:pk>/', catalogo.IpsUpdateView.as_view()),
    path('catalogo/ips/desactivar/<int:pk>/', catalogo.ips_desactivar, name='ips_delete'),

    # JefeTic
    path('catalogo/jefetic/', catalogo.JefeTicListView.as_view(), name='jefetic_list'),
    path('catalogo/jefetic/crear/', catalogo.JefeTicCreateView.as_view(), name='jefetic_create'),
    path('catalogo/jefetic/<int:pk>/editar/', catalogo.JefeTicUpdateView.as_view(), name='jefetic_update'),
    path('catalogo/jefetic/<int:pk>/desactivar/', catalogo.jefetic_desactivar, name='jefetic_deactivate'),
    path('catalogo/jefetic/nuevo/', catalogo.JefeTicCreateView.as_view()),
    path('catalogo/jefetic/editar/<int:pk>/', catalogo.JefeTicUpdateView.as_view()),
    path('catalogo/jefetic/desactivar/<int:pk>/', catalogo.jefetic_desactivar, name='jefetic_delete'),

    # Modelo
    path('catalogo/modelo/', catalogo.ModeloListView.as_view(), name='modelo_list'),
    path('catalogo/modelo/crear/', catalogo.ModeloCreateView.as_view(), name='modelo_create'),
    path('catalogo/modelo/<int:pk>/editar/', catalogo.ModeloUpdateView.as_view(), name='modelo_update'),
    path('catalogo/modelo/<int:pk>/desactivar/', catalogo.modelo_desactivar, name='modelo_deactivate'),
    path('catalogo/modelo/nuevo/', catalogo.ModeloCreateView.as_view()),
    path('catalogo/modelo/editar/<int:pk>/', catalogo.ModeloUpdateView.as_view()),
    path('catalogo/modelo/desactivar/<int:pk>/', catalogo.modelo_desactivar, name='modelo_delete'),

    # Propietario
    path('catalogo/propietario/', catalogo.PropietarioListView.as_view(), name='propietario_list'),
    path('catalogo/propietario/crear/', catalogo.PropietarioCreateView.as_view(), name='propietario_create'),
    path('catalogo/propietario/<int:pk>/editar/', catalogo.PropietarioUpdateView.as_view(), name='propietario_update'),
    path('catalogo/propietario/<int:pk>/desactivar/', catalogo.propietario_desactivar, name='propietario_deactivate'),
    path('catalogo/propietario/nuevo/', catalogo.PropietarioCreateView.as_view()),
    path('catalogo/propietario/editar/<int:pk>/', catalogo.PropietarioUpdateView.as_view()),
    path('catalogo/propietario/desactivar/<int:pk>/', catalogo.propietario_desactivar, name='propietario_delete'),

    # Contrato
    path('catalogo/contrato/', catalogo.ContratoListView.as_view(), name='contrato_list'),
    path('catalogo/contrato/crear/', catalogo.ContratoCreateView.as_view(), name='contrato_create'),
    path('catalogo/contrato/<int:pk>/editar/', catalogo.ContratoUpdateView.as_view(), name='contrato_update'),
    path('catalogo/contrato/<int:pk>/desactivar/', catalogo.contrato_desactivar, name='contrato_deactivate'),
    path('catalogo/contrato/nuevo/', catalogo.ContratoCreateView.as_view()),
    path('catalogo/contrato/editar/<int:pk>/', catalogo.ContratoUpdateView.as_view()),
    path('catalogo/contrato/desactivar/<int:pk>/', catalogo.contrato_desactivar, name='contrato_delete'),

    # Accesorio
    path('catalogo/accesorio/', catalogo.AccesorioListView.as_view(), name='accesorio_list'),
    path('catalogo/accesorio/crear/', catalogo.AccesorioCreateView.as_view(), name='accesorio_create'),
    path('catalogo/accesorio/<int:pk>/editar/', catalogo.AccesorioUpdateView.as_view(), name='accesorio_update'),
    path('catalogo/accesorio/<int:pk>/desactivar/', catalogo.accesorio_desactivar, name='accesorio_deactivate'),
    path('catalogo/accesorio/nuevo/', catalogo.AccesorioCreateView.as_view()),
    path('catalogo/accesorio/editar/<int:pk>/', catalogo.AccesorioUpdateView.as_view()),
    path('catalogo/accesorio/desactivar/<int:pk>/', catalogo.accesorio_desactivar, name='accesorio_delete'),

    # Tipo Activo
    path('tipo-activo/', tipo_activo.TipoActivoListView.as_view(), name='tipo_activo_list'),
    path('tipo-activo/nuevo/', tipo_activo.TipoActivoCreateView.as_view(), name='tipo_activo_create'),
    path('tipo-activo/editar/<int:pk>/', tipo_activo.TipoActivoUpdateView.as_view(), name='tipo_activo_update'),
    path('tipo-activo/desactivar/<int:pk>/', tipo_activo.tipo_activo_desactivar, name='tipo_activo_delete'),

    path('campos-tipo-activos/', campos_tipo_activos.campos_tipo_activos, name='campos_tipo_activos'),
    path('movimientos-activo/', movimientos_activo.movimientos_activo, name='movimientos_activo'),
    path('movimientos-activo-list/', movimientos_activo.movimientos_activo_list, name='movimientos_activo_list'),
    path('busqueda-activo/', movimientos_activo.movimientos_busqueda, name='movimientos_busqueda'),

    path('activos-asignados/', activos.activo_list_asignado, name='activo_list_asignado'),

    # Opciones para loc campos agregados
    path('opciones-campo-activo/', opciones_campo_tipo_activo.OpcionCampoTipoActivoListView.as_view(),
         name='opcion_campo_list'),
    path('opciones-campo-activo/nuevo/', opciones_campo_tipo_activo.OpcionCampoTipoActivoCreateView.as_view(),
         name='opcion_campo_create'),
    path('opciones-campo-activo/editar/<int:pk>/',
         opciones_campo_tipo_activo.OpcionCampoTipoActivosUpdateView.as_view(),
         name='opcion_campo_update'),

    path('equipos-baja/', equipos_baja.equipos_baja, name='equipos_baja'),

    path('recepcion-conforme/<int:pk>', movimientos_activo.recepcion_conforme, name='recepcion_conforme')

]
