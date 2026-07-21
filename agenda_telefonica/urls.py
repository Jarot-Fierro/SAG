from django.urls import path

from agenda_telefonica import views

app_name = 'agenda'

urlpatterns = [
    path('', views.index, name='index'),
    path('buscar/', views.buscar_anexo, name='buscar_anexo'),
    path('anexos/', views.anexos_view, name='anexos'),
    path('anexos/nuevo/', views.anexos_view, name='anexo_nuevo'),
    path('anexos/sin-funcionario/', views.anexos_sin_funcionario_view, name='anexos_sin_funcionario'),
    path('anexos/pdf/', views.anexos_pdf_view, name='anexos_pdf'),
    path('anexos/editar/<int:pk>/', views.anexos_view, name='anexo_editar'),
    path('anexos/sin-funcionario/editar/<int:pk>/', views.anexos_sin_funcionario_view,
         name='anexo_sin_funcionario_editar'),
    path('anexos/eliminar/<int:pk>/', views.anexo_delete_view, name='anexo_delete'),

    path('listado-anexos', views.AnexoListView.as_view(), name='list_anexos'),
    path('listado-anexos-edit', views.AnexoEditListView.as_view(), name='list_anexos_edit'),

    path('mantenedores/<str:tipo>/', views.mantenedores_list_view, name='mantenedores'),
    path('mantenedores/<str:tipo>/nuevo/', views.mantenedores_create_view, name='mantenedores_create'),
    path('mantenedores/<str:tipo>/editar/<int:pk>/', views.mantenedores_update_view, name='mantenedores_update'),
]
