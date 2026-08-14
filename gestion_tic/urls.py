from django.urls import path

from .views import catalogo, tipo_activo, campos_tipo_activos, activos, movimientos_activo, pdfs
from .views import opciones_campo_tipo_activo

app_name = 'gestion_tic'

urlpatterns = [

    path('activo/acta/pdf/<int:pk>/', pdfs.generar_acta_activo, name='activo_acta_pdf'),

    # Activos
    path('activos/', activos.activo_list, name='activo_list'),
    path('activos/nuevo/', activos.activo_create, name='activo_create'),
    path('activos/editar/<int:pk>/', activos.activo_edit, name='activo_edit'),

    # Marca
    path('catalogo/marca/', catalogo.MarcaListView.as_view(), name='marca_list'),
    path('catalogo/marca/nuevo/', catalogo.MarcaCreateView.as_view(), name='marca_create'),
    path('catalogo/marca/editar/<int:pk>/', catalogo.MarcaUpdateView.as_view(), name='marca_update'),
    path('catalogo/marca/desactivar/<int:pk>/', catalogo.marca_desactivar, name='marca_delete'),

    # Ips
    path('catalogo/ips/', catalogo.IpsListView.as_view(), name='ips_list'),
    path('catalogo/ips/nuevo/', catalogo.IpsCreateView.as_view(), name='ips_create'),
    path('catalogo/ips/editar/<int:pk>/', catalogo.IpsUpdateView.as_view(), name='ips_update'),
    path('catalogo/ips/desactivar/<int:pk>/', catalogo.ips_desactivar, name='ips_delete'),

    # JefeTic
    path('catalogo/jefetic/', catalogo.JefeTicListView.as_view(), name='jefetic_list'),
    path('catalogo/jefetic/nuevo/', catalogo.JefeTicCreateView.as_view(), name='jefetic_create'),
    path('catalogo/jefetic/editar/<int:pk>/', catalogo.JefeTicUpdateView.as_view(), name='jefetic_update'),
    path('catalogo/jefetic/desactivar/<int:pk>/', catalogo.jefetic_desactivar, name='jefetic_delete'),

    # Modelo
    path('catalogo/modelo/', catalogo.ModeloListView.as_view(), name='modelo_list'),
    path('catalogo/modelo/nuevo/', catalogo.ModeloCreateView.as_view(), name='modelo_create'),
    path('catalogo/modelo/editar/<int:pk>/', catalogo.ModeloUpdateView.as_view(), name='modelo_update'),
    path('catalogo/modelo/desactivar/<int:pk>/', catalogo.modelo_desactivar, name='modelo_delete'),

    # Propietario
    path('catalogo/propietario/', catalogo.PropietarioListView.as_view(), name='propietario_list'),
    path('catalogo/propietario/nuevo/', catalogo.PropietarioCreateView.as_view(), name='propietario_create'),
    path('catalogo/propietario/editar/<int:pk>/', catalogo.PropietarioUpdateView.as_view(), name='propietario_update'),
    path('catalogo/propietario/desactivar/<int:pk>/', catalogo.propietario_desactivar, name='propietario_delete'),

    # Contrato
    path('catalogo/contrato/', catalogo.ContratoListView.as_view(), name='contrato_list'),
    path('catalogo/contrato/nuevo/', catalogo.ContratoCreateView.as_view(), name='contrato_create'),
    path('catalogo/contrato/editar/<int:pk>/', catalogo.ContratoUpdateView.as_view(), name='contrato_update'),
    path('catalogo/contrato/desactivar/<int:pk>/', catalogo.contrato_desactivar, name='contrato_delete'),

    # Tipo Activo
    path('tipo-activo/', tipo_activo.TipoActivoListView.as_view(), name='tipo_activo_list'),
    path('tipo-activo/nuevo/', tipo_activo.TipoActivoCreateView.as_view(), name='tipo_activo_create'),
    path('tipo-activo/editar/<int:pk>/', tipo_activo.TipoActivoUpdateView.as_view(), name='tipo_activo_update'),
    path('tipo-activo/desactivar/<int:pk>/', tipo_activo.tipo_activo_desactivar, name='tipo_activo_delete'),

    path('campos-tipo-activos/', campos_tipo_activos.campos_tipo_activos, name='campos_tipo_activos'),
    path('movimientos-activo/', movimientos_activo.movimientos_activo, name='movimientos_activo'),
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

]
