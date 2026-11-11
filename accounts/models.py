from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from .validators import validar_rut


class Perfil(models.Model):
    """Datos complementarios del usuario (RUT, teléfono y rol institucional)."""

    class Rol(models.TextChoices):
        CLIENTE = 'CLIENTE', 'Cliente / Viajero'
        GUIA = 'GUIA', 'Guía de turismo'
        ADMINISTRATIVO = 'ADMIN', 'Personal administrativo'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil'
    )
    rut = models.CharField('RUT', max_length=12, unique=True, validators=[validar_rut])
    telefono = models.CharField(
        'Teléfono', max_length=15, blank=True,
        validators=[RegexValidator(r'^\+?\d{8,14}$', 'Ingresa un teléfono válido, ej: +56912345678')],
    )
    rol = models.CharField('Rol institucional', max_length=10, choices=Rol.choices, default=Rol.CLIENTE)

    class Meta:
        verbose_name = 'perfil'
        verbose_name_plural = 'perfiles'

    def __str__(self):
        return f'Perfil de {self.user.get_username()} ({self.get_rol_display()})'
