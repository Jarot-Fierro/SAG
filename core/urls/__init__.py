from django.urls import path, include

urlpatterns = [
    path('', include('core.urls.intranet')),
    path('usuarios/', include('core.urls.usuarios')),
    path('funcionarios/', include('core.urls.funcionarios')),
]
