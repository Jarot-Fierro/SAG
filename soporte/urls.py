from django.urls import path

from soporte.views.panel_ticket import *
from soporte.views.tickets import *

app_name = 'soporte'

urlpatterns = [
    # TICKETS estos 3 son para el usuario de SOPORTE
    path('soporte-tickets/crear/', TicketCreateView.as_view(), name='ticket_create'),
    path('soporte-tickets/editar/<int:pk>', TicketsUpdateView.as_view(), name='ticket_update'),
    # PANEL DE TICKETS
    path('soporte-tickets-panel/crear/', PanelTicketCreateView.as_view(), name='ticket_panel_create'),
    path('soporte-tickets-panel/editar/<int:pk>', PanelTicketsUpdateView.as_view(), name='ticket_panel_update'),
]
