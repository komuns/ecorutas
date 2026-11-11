from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    # LogoutView solo acepta POST (Django 5): el botón del navbar es un formulario con CSRF.
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
