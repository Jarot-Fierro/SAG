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
    # path('mantenedores/<str:tipo>/', mantenedores, name='mantenedores'),
    # path('mantenedores/<str:tipo>/buscar/', buscar_mantenedor, name='buscar_mantenedor'),
    # path('mantenedores/<str:tipo>/eliminar/<int:pk>/', eliminar_mantenedor, name='eliminar_mantenedor'),
    # path('organigrama/', organigrama, name='organigrama'),
]
