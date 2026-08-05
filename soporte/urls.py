from django.urls import path

from soporte.views.tickets import *

app_name = 'soporte'

urlpatterns = [
    # DASHBOARD
    path('soporte-tickets/dashboard/', TicketDashboardView.as_view(), name='ticket_dashboard'),

    # TICKETS
    path('soporte-tickets/lista/', TicketListView.as_view(), name='ticket_list'),
    path('soporte-tickets/crear/', TicketCreateView.as_view(), name='ticket_create'),
    path('soporte-tickets/editar/<int:pk>', TicketsUpdateView.as_view(), name='ticket_update'),
    path('soporte-tickets/eliminar/<int:pk>/', ticket_delete, name='ticket_delete'),

    # TICKETS MODO EDITOR
    path('soporte-tickets-editor/lista/', TicketEditorListView.as_view(), name='ticket_editor_list'),
    path('soporte-detail/<int:pk>/', TicketDetailView.as_view(), name='ticket_detail'),
    path('soporte-tomar/ticket/<int:pk>/', ticket_tomar, name='ticket_tomar'),
    path('soporte-cerrar/ticket/<int:pk>/', ticket_cerrar, name='ticket_cerrar'),
    path('soporte-tickets-inactivos/lista/', TicketEditorInactivosListView.as_view(), name='ticket_inactivos_list'),
]
