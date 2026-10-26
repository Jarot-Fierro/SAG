from django.urls import path

from agenda_telefonica import views

app_name = 'agenda'

urlpatterns = [
    path('', views.IndexView.as_view(), name='list_anexos'),
    path('listado-anexos-edit', views.ListEditAnexosView.as_view(), name='list_anexos_edit'),
    path('crear-anexo', views.AnexosCreateView.as_view(), name='crear_anexo'),
    path('editar-anexo/<int:pk>/', views.AnexosUpdateView.as_view(), name='editar_anexo'),
    path('eliminar-anexo/<int:pk>/', views.anexos_eliminar, name='eliminar_anexo'),
]
