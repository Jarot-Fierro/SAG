from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .middleware import CONTRATOS_AVISO_SESION


@receiver(user_logged_in, dispatch_uid='inventario_tic_reiniciar_aviso_contratos')
def reiniciar_aviso_contratos(sender, request, **kwargs):
    if request is not None:
        request.session.pop(CONTRATOS_AVISO_SESION, None)
