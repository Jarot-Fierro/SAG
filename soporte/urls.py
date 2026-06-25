from django.urls import path

from soporte.views.tickets import *

app_name = 'soporte'

urlpatterns = [

    # TICKETS estos 3 son para el usuario de SOPORTE
    path('soporte-tickets/crear/', TicketCreateView.as_view(), name='ticket_create'),
    path('soporte-tickets/editar/<int:pk>', TicketsUpdateView.as_view(), name='ticket_update'),
]
