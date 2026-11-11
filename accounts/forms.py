from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction

from .models import Perfil
from .validators import normalizar_rut, validar_rut


class RegistroForm(UserCreationForm):
    """Registro de usuario + perfil (RUT y teléfono)."""

    first_name = forms.CharField(label='Nombre', max_length=150)
    last_name = forms.CharField(label='Apellido', max_length=150)
    email = forms.EmailField(label='Correo electrónico')
    rut = forms.CharField(label='RUT', max_length=12, help_text='Ej: 12345678-5', validators=[validar_rut])
    telefono = forms.CharField(label='Teléfono', max_length=15, required=False, help_text='Ej: +56912345678')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault('class', 'form-control')

    def clean_rut(self):
        rut = normalizar_rut(self.cleaned_data['rut'])
        if Perfil.objects.filter(rut=rut).exists():
            raise forms.ValidationError('Ya existe un usuario registrado con este RUT.')
        return rut

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este correo ya está registrado.')
        return email

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=True)
        Perfil.objects.create(
            user=user,
            rut=self.cleaned_data['rut'],
            telefono=self.cleaned_data.get('telefono', ''),
            rol=Perfil.Rol.CLIENTE,
        )
        return user
