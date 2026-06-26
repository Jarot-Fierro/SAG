import time

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect

from core.forms.usuarios import RegistroForm
from core.models import User


def login_view(request):
    if request.user.is_authenticated:
        return redirect('intranet:index')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Lógica de "Recuérdame"
            if request.POST.get('remember_me'):
                # Si marca recuérdame, la sesión dura 2 semanas (valor por defecto de Django si no se especifica) 
                # o podemos dejar que use el SESSION_COOKIE_AGE definido si es persistente.
                # Al no llamar a set_expiry(0), se usa el valor de SESSION_COOKIE_AGE.
                request.session.set_expiry(None)
            else:
                # Si no marca recuérdame, la sesión expira al cerrar el navegador
                request.session.set_expiry(0)

            return redirect('intranet:index')
    else:
        form = AuthenticationForm()

    return render(request, 'base_login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def perfil_view(request):
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '').upper()
        user.last_name = request.POST.get('last_name', '').upper()
        user.email = request.POST.get('email', '').lower()
        user.save()
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('perfil')

    modulos = user.modulos.all()
    return render(request, 'usuarios/perfil.html', {
        'user': user,
        'modulos': modulos
    })


@login_required
def cambiar_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request,
                                     user)  # Importante para no desloguear si no se quiere, pero el usuario pidió que se desloguee.
            # El usuario pidió: "al cambiarla se desloguea de la sessión"
            logout(request)
            messages.success(request, 'Contraseña cambiada correctamente. Por favor, inicia sesión de nuevo.')
            return redirect('login')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'usuarios/cambiar_password.html', {'form': form})


def registro_view(request):
    if request.user.is_authenticated:
        return redirect('intranet:index')

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.info(request,
                          'Su cuenta quedará inactiva hasta que un administrador apruebe su registro. Mientras tanto no puede iniciar sesión.')
            return redirect('login')
    else:
        form = RegistroForm()


@login_required
def buscar_funcionario_ajax(request):
    """
    Busca funcionarios (usuarios) de forma precisa por nombre + apellido o username (RUT).
    Incluye un delay de 250ms para optimizar las consultas al servidor.
    Permite filtrar por establecimiento del usuario logueado y opcionalmente por departamento.
    """
    time.sleep(0.25)  # Delay de 250ms solicitado

    q = (request.GET.get('q') or request.GET.get('term') or '').upper()
    # Si viene departamento_id en el GET, se usa ese, sino se usa el del usuario logueado.
    departamento_id = request.GET.get('departamento_id') or request.user.departamento_id

    # Base queryset: Usuarios activos
    queryset = User.objects.filter(is_active=True)

    # El usuario logueado debe pertenecer a un establecimiento para filtrar, 
    # de lo contrario podría ser un superusuario o alguien sin establecimiento asignado.
    if request.user.establecimiento_id:
        queryset = queryset.filter(establecimiento=request.user.establecimiento)

    # Filtro por departamento
    if departamento_id:
        queryset = queryset.filter(departamento_id=departamento_id)

    if q:
        # Búsqueda por username (RUT), o nombre/apellido (o combinación)
        q_parts = q.split(' ')
        if len(q_parts) > 1:
            # Si hay más de una palabra, buscamos por combinación de nombre y apellido
            queryset = queryset.filter(
                Q(username__icontains=q) |
                (Q(first_name__icontains=q_parts[0]) & Q(last_name__icontains=' '.join(q_parts[1:]))) |
                (Q(first_name__icontains=' '.join(q_parts[:-1])) & Q(last_name__icontains=q_parts[-1]))
            )
        else:
            queryset = queryset.filter(
                Q(username__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)
            )

    results = []
    for user in queryset[:20]:  # Limitar resultados por rendimiento
        results.append({
            'id': user.id,
            'text': f"{user.first_name} {user.last_name}"
        })

    return JsonResponse({'results': results})
