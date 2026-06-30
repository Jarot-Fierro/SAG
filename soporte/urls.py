from django.urls import path

from soporte.views.tickets import *

app_name = 'soporte'

urlpatterns = [
    # TICKETS
    path('soporte-tickets/lista/', list_tickets, name='ticket_list'),
    path('soporte-tickets/crear/', TicketCreateView.as_view(), name='ticket_create'),
    path('soporte-tickets/editar/<int:pk>', TicketsUpdateView.as_view(), name='ticket_update'),
    path('soporte-tickets/editar-editor/<int:pk>', TicketEditorUpdateView.as_view(), name='ticket_editor_update'),
    path('soporte-tickets/eliminar/<int:pk>/', ticket_delete, name='ticket_delete'),

]
