from gestion_tic.models.tipo_activo import TipoActivo


def menu_activos(request):
    if request.user.is_authenticated:
        # Si el modelo Activo usa StandardModelEstablishment, tiene el campo 'establecimiento'
        # y probablemente 'is_active'
        activos = TipoActivo.objects.filter(
            establecimiento=request.user.establecimiento,
            is_active=True
        ).order_by('nombre')
        return {'sidebar_activos': activos}
    return {'sidebar_activos': []}
