from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .decorators import perfil_horos_required
from .models import PerfilHoros


@login_required
@perfil_horos_required
def accesos_horos(request):
    perfil = PerfilHoros.objects.get(usuario=request.user)
    accesos = perfil.acceso.filter(is_active=True)
    return render(request, 'horos/accessos.html', {'accesos': accesos})
