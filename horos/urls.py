from django.urls import path

from horos.views import *

app_name = 'horos'

urlpatterns = [
    path('accesos/', accesos_horos, name='accesos_horos'),

]
