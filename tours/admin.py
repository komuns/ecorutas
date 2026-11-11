from django.contrib import admin

from .models import RegionTuristica, TourExpedicion

# --- Identidad corporativa -------------------------------------------------
admin.site.site_header = 'EcoRutas Chile - Panel de Control'
admin.site.site_title = 'EcoRutas Chile Admin'
admin.site.index_title = 'Gestión Operativa de Recursos y Servicios'


@admin.register(RegionTuristica)
class RegionTuristicaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'clima', 'temporada_recomendada')
    search_fields = ('nombre', 'descripcion')
    prepopulated_fields = {'slug': ('nombre',)}


@admin.register(TourExpedicion)
class TourExpedicionAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'titulo', 'region', 'tarifa_por_persona', 'cupos', 'estado', 'activo')
    list_display_links = ('codigo', 'titulo')
    list_filter = ('region', 'estado', 'activo', 'dificultad')
    search_fields = ('codigo', 'titulo', 'descripcion')
    list_editable = ('tarifa_por_persona', 'cupos', 'estado')  # edición rápida en la grilla
    list_select_related = ('region',)
    prepopulated_fields = {'slug': ('codigo', 'titulo')}
    date_hierarchy = 'fecha_salida'
    actions = ['dar_de_baja', 'reactivar']

    fieldsets = (
        ('Identificación', {'fields': ('region', 'codigo', 'slug', 'titulo')}),
        ('Descripción del tour', {'fields': ('descripcion', 'punto_encuentro', 'requisitos')}),
        ('Tarifas y capacidad', {'fields': ('tarifa_por_persona', 'cupos', 'duracion_dias', 'fecha_salida')}),
        ('Condición operativa', {'fields': ('dificultad', 'estado', 'activo')}),
        ('Multimedia', {'fields': ('imagen',)}),
    )

    @admin.action(description='Dar de baja los tours seleccionados (baja lógica)')
    def dar_de_baja(self, request, queryset):
        n = queryset.update(activo=False)
        self.message_user(request, f'{n} tour(s) dados de baja.')

    @admin.action(description='Reactivar los tours seleccionados')
    def reactivar(self, request, queryset):
        n = queryset.update(activo=True)
        self.message_user(request, f'{n} tour(s) reactivados.')
