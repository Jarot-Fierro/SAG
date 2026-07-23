import logging
import re

from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View

from core.forms.recuperacion_password import RecuperacionPasswordForm, ResetPasswordForm
from core.services.password_recovery_service import PasswordRecoveryService

logger = logging.getLogger(__name__)


class PasswordRecoveryRequestView(View):
    template_name = 'usuarios/recuperar_password.html'

    def get(self, request):
        form = RecuperacionPasswordForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = RecuperacionPasswordForm(request.POST)
        if form.is_valid():
            rut = form.cleaned_data['rut']
            # Si no viene formateado, lo formatea como 12.345.678-9
            if "." not in rut or "-" not in rut:
                rut = re.sub(r"[^0-9kK]", "", rut).upper()

                if len(rut) >= 2:
                    cuerpo = rut[:-1]
                    dv = rut[-1]
                    rut = f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"

            # El servicio maneja la lógica y el rate limiting
            PasswordRecoveryService.create_recovery_request(rut, request)

            # Siempre mostrar el mismo mensaje de éxito por seguridad
            return render(request, 'usuarios/recuperar_password_success.html')

        return render(request, self.template_name, {'form': form})


class PasswordResetConfirmView(View):
    template_name = 'usuarios/reset_password_confirm.html'

    def get(self, request, token):
        recovery, error_msg = PasswordRecoveryService.validate_token(token)
        if error_msg:
            return render(request, 'usuarios/reset_password_error.html',
                          {'error_msg': error_msg})

        form = ResetPasswordForm()
        return render(request, self.template_name, {'form': form, 'token': token, 'usuario': recovery.usuario})

    def post(self, request, token):
        recovery, error_msg = PasswordRecoveryService.validate_token(token)
        if error_msg:
            return render(request, 'usuarios/reset_password_error.html',
                          {'error_msg': error_msg})

        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            PasswordRecoveryService.reset_password(recovery, new_password, request)

            messages.success(request, "Su contraseña ha sido actualizada correctamente. Ahora puede iniciar sesión.")
            return redirect('usuarios:login')

        return render(request, self.template_name, {'form': form, 'token': token, 'usuario': recovery.usuario})
