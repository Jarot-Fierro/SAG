from django.urls import path

from core.views.correos import CorreoListView, CorreoCreateView, CorreoUpdateView, correo_desactivar
from core.views.establecimientos import EstablecimientoListView, EstablecimientoCreateView, EstablecimientoUpdateView, \
    establecimiento_desactivar
from core.views.modulos import ModuloListView, ModuloCreateView, ModuloUpdateView, modulo_desactivar
from core.views.profesiones import ProfesionListView, ProfesionCreateView, ProfesionUpdateView, profesion_desactivar

app_name = 'core'

urlpatterns = [
    # Módulos
    path('modulos/', ModuloListView.as_view(), name='modulo_list'),
    path('modulos/crear/', ModuloCreateView.as_view(), name='modulo_create'),
    path('modulos/editar/<int:pk>/', ModuloUpdateView.as_view(), name='modulo_update'),
    path('modulos/desactivar/<int:pk>/', modulo_desactivar, name='modulo_delete'),

    # Establecimientos
    path('establecimientos/', EstablecimientoListView.as_view(), name='establecimiento_list'),
    path('establecimientos/crear/', EstablecimientoCreateView.as_view(), name='establecimiento_create'),
    path('establecimientos/editar/<int:pk>/', EstablecimientoUpdateView.as_view(), name='establecimiento_update'),
    path('establecimientos/desactivar/<int:pk>/', establecimiento_desactivar, name='establecimiento_delete'),

    # Profesiones
    path('profesiones/', ProfesionListView.as_view(), name='profesion_list'),
    path('profesiones/crear/', ProfesionCreateView.as_view(), name='profesion_create'),
    path('profesiones/editar/<int:pk>/', ProfesionUpdateView.as_view(), name='profesion_update'),
    path('profesiones/desactivar/<int:pk>/', profesion_desactivar, name='profesion_delete'),

    # Correos
    path('correos/', CorreoListView.as_view(), name='correo_list'),
    path('correos/crear/', CorreoCreateView.as_view(), name='correo_create'),
    path('correos/editar/<int:pk>/', CorreoUpdateView.as_view(), name='correo_update'),
    path('correos/desactivar/<int:pk>/', correo_desactivar, name='correo_delete'),
]
