from django.urls import path

from core.views.usuarios import login_view, logout_view, perfil_view, cambiar_password_view, registro_view, \
    buscar_funcionario_ajax

app_name = 'usuarios'

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('perfil/', perfil_view, name='perfil'),
    path('perfil/cambiar-password/', cambiar_password_view, name='cambiar_password'),
    path('registro/', registro_view, name='registro'),
    path('buscar-funcionario-ajax/', buscar_funcionario_ajax, name='buscar_funcionario_ajax'),
]
