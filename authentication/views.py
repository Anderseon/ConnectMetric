from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import logout, login # Salida y verificaciones
from django.contrib.auth.forms import AuthenticationForm # verificacion


def login_view(request):
    if request.user.is_authenticated:
        return redirect('blog:dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user() # <-- Obtiene el usuario del formulario validado
            login(request, user)
            return redirect('blog:dashboard')
    else:
        form = AuthenticationForm()

    return render(request, 'authentication/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, "Has cerrado sesión exitosamente.")
    return redirect('/')
