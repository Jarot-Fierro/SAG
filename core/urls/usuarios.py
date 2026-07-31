from django.urls import path

from core.views.usuarios import login_view, logout_view, perfil_view, cambiar_password_view, registro_view, \
    buscar_funcionario_ajax, cambiar_establecimiento_view, UsuarioCreateView, UsuarioUpdateView, \
    UserListView

app_name = 'usuarios'

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('perfil/', perfil_view, name='perfil'),
    path('perfil/cambiar-password/', cambiar_password_view, name='cambiar_password'),
    path('registro/', registro_view, name='registro'),
    path('buscar-funcionario-ajax/', buscar_funcionario_ajax, name='buscar_funcionario_ajax'),
    path('cambiar-establecimiento/<int:establecimiento_id>/', cambiar_establecimiento_view,
         name='cambiar_establecimiento'),
    # path('lista-usuarios/', list_users, name='list_usuario'),
    path('lista-usuarios-2/', UserListView.as_view(), name='list_usuario'),
    path('crear-usuario/', UsuarioCreateView.as_view(), name='crear_usuario'),
    path('actualizar-usuario/<int:pk>/', UsuarioUpdateView.as_view(), name='actualizar_usuario')
]
