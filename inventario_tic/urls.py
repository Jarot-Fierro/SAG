from django.urls import path

from .views import mantenedores
from .views import dashboard
from .views import asignados
from .views import estaciones
from .views.celulares import (
    CelularListView,
    CelularCreateView,
    CelularUpdateView,
    celular_eliminar, CelularRecepcionUpdateView, celular_devolucion,
)
from .views.impresoras import ImpresoraListView, ImpresoraCreateView, ImpresoraUpdateView, impresora_eliminar
from .views.monitores import MonitorListView, MonitorCreateView, MonitorUpdateView, monitor_eliminar, MonitorRecepcionUpdateView, monitor_devolucion
from .views.pdfs import generar_acta_celulares, generar_acta_impresoras, generar_acta_monitores, generar_acta_computadores
from .views.productos import ProductoListView, ProductoCreateView, ProductoUpdateView, producto_eliminar

from .views.funcionarios import (
    FuncionarioInventarioListView, FuncionarioInventarioCreateView,
    FuncionarioInventarioUpdateView, funcionario_desactivar, funcionario_crear_modal,
)

from .views.computadores import (
    ComputadorListView, ComputadorCreateView, ComputadorUpdateView, computador_eliminar,
    ComputadorRecepcionUpdateView, computador_devolucion,
)

app_name = 'inventario_tic'

urlpatterns = [
    path('dashboard/', dashboard.dashboard, name='dashboard'),
    path('dashboard/datos/', dashboard.datos, name='dashboard_datos'),
    path('asignados/', asignados.listado, name='asignados_list'),
    path('estaciones/', estaciones.listado, name='estacion_list'),
    path('estaciones/asignar/', estaciones.nueva, name='estacion_create'),
    path('estaciones/buscar/', estaciones.buscar, name='estacion_buscar'),
    path('estaciones/<int:pk>/', estaciones.detalle, name='estacion_detalle'),
    path('estaciones/<int:pk>/acta/', estaciones.acta, name='estacion_acta'),
    # Computadores
    path('computadores/<int:pk>/acta/', generar_acta_computadores, name='generar_acta_computadores'),
    path('computadores/<int:pk>/recepcion/', ComputadorRecepcionUpdateView.as_view(), name='computador_recepcion_update'),
    path('computadores/<int:pk>/devolucion/', computador_devolucion, name='computador_devolucion'),
    path('computadores/', ComputadorListView.as_view(), name='computador_list'),
    path('computadores/crear/', ComputadorCreateView.as_view(), name='computador_create'),
    path('computadores/<int:pk>/editar/', ComputadorUpdateView.as_view(), name='computador_update'),
    path('computadores/<int:pk>/desactivar/', computador_eliminar, name='computador_eliminar'),
    path('mantenedores/funcionarios/', FuncionarioInventarioListView.as_view(), name='funcionario_list'),
    path('mantenedores/funcionarios/crear/', FuncionarioInventarioCreateView.as_view(), name='funcionario_create'),
    path('mantenedores/funcionarios/crear-modal/', funcionario_crear_modal, name='funcionario_create_modal'),
    path('mantenedores/funcionarios/<int:pk>/editar/', FuncionarioInventarioUpdateView.as_view(), name='funcionario_update'),
    path('mantenedores/funcionarios/<int:pk>/desactivar/', funcionario_desactivar, name='funcionario_deactivate'),
    # Monitores
    path('monitores/<int:pk>/acta/', generar_acta_monitores, name='generar_acta_monitores'),
    path('monitores/<int:pk>/recepcion/', MonitorRecepcionUpdateView.as_view(), name='monitor_recepcion_update'),
    path('monitores/<int:pk>/devolucion/', monitor_devolucion, name='monitor_devolucion'),
    path('monitores/', MonitorListView.as_view(), name='monitor_list'),
    path('monitores/crear/', MonitorCreateView.as_view(), name='monitor_create'),
    path('monitores/<int:pk>/editar/', MonitorUpdateView.as_view(), name='monitor_update'),
    path('monitores/<int:pk>/desactivar/', monitor_eliminar, name='monitor_eliminar'),
    # Impresoras
    path('impresoras/<int:pk>/acta/', generar_acta_impresoras, name='generar_acta_impresoras'),
    path('impresoras/', ImpresoraListView.as_view(), name='impresora_list'),
    path('impresoras/crear/', ImpresoraCreateView.as_view(), name='impresora_create'),
    path('impresoras/<int:pk>/editar/', ImpresoraUpdateView.as_view(), name='impresora_update'),
    path('impresoras/<int:pk>/desactivar/', impresora_eliminar, name='impresora_eliminar'),
    path('impresoras/nuevo/', ImpresoraCreateView.as_view()),
    path('impresoras/editar/<int:pk>/', ImpresoraUpdateView.as_view()),
    path('impresoras/desactivar/<int:pk>/', impresora_eliminar, name='impresora_delete'),
    # Tipos de Producto
    path('mantenedores/tipo-producto/', mantenedores.TipoProductoListView.as_view(), name='tipo_producto_list'),
    path('mantenedores/tipo-producto/crear/', mantenedores.TipoProductoCreateView.as_view(),
         name='tipo_producto_create'),
    path('mantenedores/tipo-producto/<int:pk>/editar/', mantenedores.TipoProductoUpdateView.as_view(),
         name='tipo_producto_update'),
    path('mantenedores/tipo-producto/<int:pk>/desactivar/', mantenedores.tipo_producto_desactivar,
         name='tipo_producto_deactivate'),
    # Productos
    path('productos/', ProductoListView.as_view(), name='producto_list'),
    path('productos/crear/', ProductoCreateView.as_view(), name='producto_create'),
    path('productos/<int:pk>/editar/', ProductoUpdateView.as_view(), name='producto_update'),
    path('productos/<int:pk>/desactivar/', producto_eliminar, name='producto_eliminar'),
    path('productos/nuevo/', ProductoCreateView.as_view()),
    path('productos/editar/<int:pk>/', ProductoUpdateView.as_view()),
    path('productos/desactivar/<int:pk>/', producto_eliminar, name='producto_delete'),
    path('mantenedores/establecimiento/', mantenedores.EstablecimientoListView.as_view(), name='establecimiento_list'),
    path('mantenedores/establecimiento/crear/', mantenedores.EstablecimientoCreateView.as_view(),
         name='establecimiento_create'),
    path('mantenedores/establecimiento/<int:pk>/editar/', mantenedores.EstablecimientoUpdateView.as_view(),
         name='establecimiento_update'),
    path('mantenedores/establecimiento/<int:pk>/desactivar/', mantenedores.establecimiento_desactivar,
         name='establecimiento_deactivate'),
    # Celulares
    path('celulares/<int:pk>/devolucion/', celular_devolucion, name='celular_devolucion'),
    path('celulares/<int:pk>/acta/', generar_acta_celulares, name='generar_acta_celulares'),
    path('celulares/', CelularListView.as_view(), name='celular_list'),
    path('celulares/crear/', CelularCreateView.as_view(), name='celular_create'),
    path('celulares/<int:pk>/editar/', CelularUpdateView.as_view(), name='celular_update'),
    path('celulares/<int:pk>/desactivar/', celular_eliminar, name='celular_eliminar'),
    path('celulares/nuevo/', CelularCreateView.as_view()),
    path('celulares/editar/<int:pk>/', CelularUpdateView.as_view()),
    path('celulares/desactivar/<int:pk>/', celular_eliminar, name='celular_delete'),
    path('celulares/<int:pk>/recepcion/', CelularRecepcionUpdateView.as_view(), name='celular_recepcion_update'),

    # Marca
    path('mantenedores/marca/', mantenedores.MarcaListView.as_view(), name='marca_list'),
    path('mantenedores/marca/crear/', mantenedores.MarcaCreateView.as_view(), name='marca_create'),
    path('mantenedores/marca/<int:pk>/editar/', mantenedores.MarcaUpdateView.as_view(), name='marca_update'),
    path('mantenedores/marca/<int:pk>/desactivar/', mantenedores.marca_desactivar, name='marca_deactivate'),
    path('mantenedores/marca/nuevo/', mantenedores.MarcaCreateView.as_view()),
    path('mantenedores/marca/editar/<int:pk>/', mantenedores.MarcaUpdateView.as_view()),
    path('mantenedores/marca/desactivar/<int:pk>/', mantenedores.marca_desactivar, name='marca_delete'),

    # Ips
    path('mantenedores/ips/', mantenedores.IpsListView.as_view(), name='ips_list'),
    path('mantenedores/ips/crear/', mantenedores.IpsCreateView.as_view(), name='ips_create'),
    path('mantenedores/ips/<int:pk>/editar/', mantenedores.IpsUpdateView.as_view(), name='ips_update'),
    path('mantenedores/ips/<int:pk>/desactivar/', mantenedores.ips_desactivar, name='ips_deactivate'),
    path('mantenedores/ips/nuevo/', mantenedores.IpsCreateView.as_view()),
    path('mantenedores/ips/editar/<int:pk>/', mantenedores.IpsUpdateView.as_view()),
    path('mantenedores/ips/desactivar/<int:pk>/', mantenedores.ips_desactivar, name='ips_delete'),

    # JefeTic
    path('mantenedores/jefetic/', mantenedores.JefeTicListView.as_view(), name='jefetic_list'),
    path('mantenedores/jefetic/crear/', mantenedores.JefeTicCreateView.as_view(), name='jefetic_create'),
    path('mantenedores/jefetic/<int:pk>/editar/', mantenedores.JefeTicUpdateView.as_view(), name='jefetic_update'),
    path('mantenedores/jefetic/<int:pk>/desactivar/', mantenedores.jefetic_desactivar, name='jefetic_deactivate'),
    path('mantenedores/jefetic/nuevo/', mantenedores.JefeTicCreateView.as_view()),
    path('mantenedores/jefetic/editar/<int:pk>/', mantenedores.JefeTicUpdateView.as_view()),
    path('mantenedores/jefetic/desactivar/<int:pk>/', mantenedores.jefetic_desactivar, name='jefetic_delete'),

    # Modelo
    path('mantenedores/modelo/', mantenedores.ModeloListView.as_view(), name='modelo_list'),
    path('mantenedores/modelo/crear/', mantenedores.ModeloCreateView.as_view(), name='modelo_create'),
    path('mantenedores/modelo/<int:pk>/editar/', mantenedores.ModeloUpdateView.as_view(), name='modelo_update'),
    path('mantenedores/modelo/<int:pk>/desactivar/', mantenedores.modelo_desactivar, name='modelo_deactivate'),
    path('mantenedores/modelo/nuevo/', mantenedores.ModeloCreateView.as_view()),
    path('mantenedores/modelo/editar/<int:pk>/', mantenedores.ModeloUpdateView.as_view()),
    path('mantenedores/modelo/desactivar/<int:pk>/', mantenedores.modelo_desactivar, name='modelo_delete'),

    # Propietario
    path('mantenedores/propietario/', mantenedores.PropietarioListView.as_view(), name='propietario_list'),
    path('mantenedores/propietario/crear/', mantenedores.PropietarioCreateView.as_view(), name='propietario_create'),
    path('mantenedores/propietario/<int:pk>/editar/', mantenedores.PropietarioUpdateView.as_view(),
         name='propietario_update'),
    path('mantenedores/propietario/<int:pk>/desactivar/', mantenedores.propietario_desactivar,
         name='propietario_deactivate'),
    path('mantenedores/propietario/nuevo/', mantenedores.PropietarioCreateView.as_view()),
    path('mantenedores/propietario/editar/<int:pk>/', mantenedores.PropietarioUpdateView.as_view()),
    path('mantenedores/propietario/desactivar/<int:pk>/', mantenedores.propietario_desactivar,
         name='propietario_delete'),

    # Contrato
    path('mantenedores/contrato/', mantenedores.ContratoListView.as_view(), name='contrato_list'),
    path('mantenedores/contrato/crear/', mantenedores.ContratoCreateView.as_view(), name='contrato_create'),
    path('mantenedores/contrato/<int:pk>/editar/', mantenedores.ContratoUpdateView.as_view(), name='contrato_update'),
    path('mantenedores/contrato/<int:pk>/desactivar/', mantenedores.contrato_desactivar, name='contrato_deactivate'),
    path('mantenedores/contrato/nuevo/', mantenedores.ContratoCreateView.as_view()),
    path('mantenedores/contrato/editar/<int:pk>/', mantenedores.ContratoUpdateView.as_view()),
    path('mantenedores/contrato/desactivar/<int:pk>/', mantenedores.contrato_desactivar, name='contrato_delete'),

]
