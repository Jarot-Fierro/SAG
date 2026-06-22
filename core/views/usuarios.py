from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.shortcuts import render, redirect

from core.forms.usuarios import RegistroForm


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

    return render(request, 'usuarios/registro.html', {'form': form})
