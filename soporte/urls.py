from django.urls import path

from soporte.views import *

app_name = 'soporte'

urlpatterns = [
    # DASHBOARD
    path('listado-soporte/', TicketListView.as_view(), name='list_soportes'),
    path('solicitud-de-soporte/', TicketCreateView.as_view(), name='create_soportes'),
    path('gestion-soporte/', ListEditTicketView.as_view(), name='ticket_editor_list'),
    path('ticket/<int:pk>/editar/', TicketUpdateView.as_view(), name='ticket_update'),
    path('ticket/<int:pk>/eliminar/', tickets_eliminar, name='ticket_delete'),
    path('ticket/<int:pk>/tomar/', ticket_tomar, name='ticket_tomar'),
    path('ticket/<int:pk>/cerrar/', ticket_cerrar, name='ticket_cerrar'),
]
