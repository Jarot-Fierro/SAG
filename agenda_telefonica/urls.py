from django.urls import path

from agenda_telefonica.views import anexos_view, eliminar_anexo

app_name = 'agenda'

urlpatterns = [
    path('anexos/', anexos_view, name='anexos'),
    path('anexos/editar/<int:pk>/', anexos_view, name='anexo_editar'),
    path('anexos/eliminar/<int:pk>/', eliminar_anexo, name='anexo_eliminar'),
]
