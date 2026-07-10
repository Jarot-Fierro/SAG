from django.urls import path

from core.views.intranet import intranet, mantenimiento_view
from core.views.organizacion import unidad_organizacional_grafico

app_name = 'intranet'

urlpatterns = [
    path('', intranet, name='index'),
    path('mantenimiento/', mantenimiento_view, name='mantenimiento'),
    path('organigrama/', unidad_organizacional_grafico, name='organigrama'),
]
