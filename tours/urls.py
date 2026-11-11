from django.urls import path

from . import views

app_name = 'tours'

urlpatterns = [
    # Público
    path('', views.catalogo, name='catalogo'),
    path('tour/<slug:slug>/', views.detalle, name='detalle'),
    path('acceso-denegado/', views.acceso_denegado, name='acceso_denegado'),
    # Backoffice (staff)
    path('gestion/', views.gestion_lista, name='gestion'),
    path('gestion/nuevo/', views.tour_crear, name='crear'),
    path('gestion/<slug:slug>/editar/', views.tour_editar, name='editar'),
    path('gestion/<slug:slug>/eliminar/', views.tour_eliminar, name='eliminar'),
    path('gestion/<slug:slug>/reactivar/', views.tour_reactivar, name='reactivar'),
    # Itinerario en sesión
    path('itinerario/', views.itinerario_ver, name='itinerario'),
    path('itinerario/agregar/<int:pk>/', views.itinerario_agregar, name='itinerario_agregar'),
    path('itinerario/actualizar/<int:pk>/', views.itinerario_actualizar, name='itinerario_actualizar'),
    path('itinerario/quitar/<int:pk>/', views.itinerario_quitar, name='itinerario_quitar'),
    path('itinerario/vaciar/', views.itinerario_vaciar, name='itinerario_vaciar'),
    path('itinerario/confirmar/', views.itinerario_confirmar, name='itinerario_confirmar'),
]
