from core.models.establecimientos import Establecimiento


def establecimientos_processor(request):
    if request.user.is_authenticated:
        return {
            'global_establecimientos': Establecimiento.objects.filter(is_active=True).order_by('nombre')
        }
    return {}
