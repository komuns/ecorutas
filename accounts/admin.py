from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Perfil


class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Perfil (RUT, teléfono y rol)'


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [PerfilInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'rol')
    list_select_related = ('perfil',)

    @admin.display(description='Rol')
    def rol(self, obj):
        return obj.perfil.get_rol_display() if hasattr(obj, 'perfil') else '—'
