from django.urls import path

from core.views.funcionarios import (
    FuncionarioCreateView,
    FuncionarioListView,
    FuncionarioUpdateView,
    funcionario_delete_view,
)

app_name = 'funcionarios'

urlpatterns = [
    path('lista/', FuncionarioListView.as_view(), name='list_funcionarios'),
    path('nuevo/', FuncionarioCreateView.as_view(), name='create_funcionario'),
    path('editar/<int:pk>/', FuncionarioUpdateView.as_view(), name='update_funcionario'),
    path('eliminar/<int:pk>/', funcionario_delete_view, name='delete_funcionario'),
]
