from django.urls import path

from core.views.intranet import intranet

app_name = 'intranet'

urlpatterns = [
    path('', intranet, name='index'),
]
