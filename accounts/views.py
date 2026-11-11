from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import RegistroForm


def registro(request):
    if request.user.is_authenticated:
        return redirect('tours:catalogo')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'¡Bienvenido/a a EcoRutas, {user.first_name}!')
            return redirect('tours:catalogo')
    else:
        form = RegistroForm()
    return render(request, 'registration/registro.html', {'form': form})
