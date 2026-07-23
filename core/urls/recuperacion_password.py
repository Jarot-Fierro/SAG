from django.urls import path

from core.views.recuperacion_password import PasswordRecoveryRequestView, PasswordResetConfirmView

app_name = 'recuperacion_password'
urlpatterns = [
    path('recuperar-password/', PasswordRecoveryRequestView.as_view(), name='password_recovery_request'),
    path('reset-password/<str:token>/', PasswordResetConfirmView.as_view(), name='reset_password'),
]
