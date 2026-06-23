from django.urls import path

from agenda_telefonica.views import *

app_name = 'agenda'

urlpatterns = [
    path('', index, name='index'),
    path('editor/', editor, name='editor'),
    path('editor/buscar/', buscar_anexo_editor, name='buscar_anexo_editor'),
    path('editor/guardar/', guardar_anexo, name='guardar_anexo'),
    path('editor/guardar/<int:pk>/', guardar_anexo, name='editar_anexo'),
    path('editor/editar/<int:pk>/', editar_anexo_form, name='editar_anexo_form'),
    path('editor/eliminar/<int:pk>/', eliminar_anexo, name='eliminar_anexo'),
    path('buscar/', buscar_anexo, name='buscar_anexo'),
]
