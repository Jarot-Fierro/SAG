from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def intranet(request):
    modulos = request.user.modulos.filter(is_active=True)
    return render(request, 'intranet/index.html', {'modulos': modulos})
