from django.urls import path

from agenda_telefonica.views import anexos_view, eliminar_anexo, index, buscar_anexo, anexos_pdf_view, \
    anexos_sin_funcionario_view

app_name = 'agenda'

urlpatterns = [
    path('', index, name='index'),
    path('buscar/', buscar_anexo, name='buscar_anexo'),
    path('anexos/', anexos_view, name='anexos'),
    path('anexos/sin-funcionario/', anexos_sin_funcionario_view, name='anexos_sin_funcionario'),
    path('anexos/pdf/', anexos_pdf_view, name='anexos_pdf'),
    path('anexos/editar/<int:pk>/', anexos_view, name='anexo_editar'),
    path('anexos/sin-funcionario/editar/<int:pk>/', anexos_sin_funcionario_view, name='anexo_sin_funcionario_editar'),
    path('anexos/eliminar/<int:pk>/', eliminar_anexo, name='anexo_eliminar'),
]
