from django.urls import path

from core.views.intranet import intranet, mantenimiento_view

app_name = 'intranet'

urlpatterns = [
    path('', intranet, name='index'),
    path('mantenimiento/', mantenimiento_view, name='mantenimiento'),
]
