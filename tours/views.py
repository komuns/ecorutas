import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import TourForm
from .itinerario import Itinerario
from .models import RegionTuristica, TourExpedicion

ORDENES = {
    'titulo': 'titulo',
    'precio_asc': 'tarifa_por_persona',
    'precio_desc': '-tarifa_por_persona',
    'duracion': 'duracion_dias',
    'fecha': 'fecha_salida',
}


def es_staff(user):
    return user.is_active and user.is_staff


# Decoradores combinados: debe estar autenticado Y ser staff.
def staff_requerido(vista):
    return login_required(user_passes_test(es_staff, login_url='tours:acceso_denegado')(vista))


# ===================== LECTURA (público) =====================
def catalogo(request):
    tours = TourExpedicion.objects.filter(activo=True).select_related('region')

    q = request.GET.get('q', '').strip()
    region = request.GET.get('region', '')
    orden = request.GET.get('orden', 'titulo')

    if q:  # búsqueda multi-campo con objetos Q
        tours = tours.filter(
            Q(titulo__icontains=q) | Q(codigo__icontains=q) | Q(descripcion__icontains=q)
        )
    if region:
        tours = tours.filter(region__slug=region)
    tours = tours.order_by(ORDENES.get(orden, 'titulo'), 'codigo')

    page_obj = Paginator(tours, 6).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)  # para conservar filtros en los links de paginación

    return render(request, 'tours/catalogo.html', {
        'page_obj': page_obj,
        'regiones': RegionTuristica.objects.all(),
        'q': q, 'region_sel': region, 'orden_sel': orden,
        'ordenes': [('titulo', 'Nombre (A-Z)'), ('precio_asc', 'Precio: menor a mayor'),
                    ('precio_desc', 'Precio: mayor a menor'), ('duracion', 'Duración'),
                    ('fecha', 'Próxima salida')],
        'querystring': params.urlencode(),
    })


def detalle(request, slug):
    filtros = {'slug': slug}
    if not (request.user.is_authenticated and request.user.is_staff):
        filtros['activo'] = True  # los dados de baja solo los ve el personal
    tour = get_object_or_404(TourExpedicion.objects.select_related('region'), **filtros)
    en_itinerario = Itinerario(request).datos.get(str(tour.pk), 0)
    return render(request, 'tours/detalle.html', {'tour': tour, 'en_itinerario': en_itinerario})


def acceso_denegado(request):
    return render(request, 'tours/acceso_denegado.html', status=403)


# ===================== BACKOFFICE (solo staff) =====================
@staff_requerido
def gestion_lista(request):
    tours = TourExpedicion.objects.select_related('region').order_by('-activo', 'region__nombre', 'codigo')
    return render(request, 'tours/gestion.html', {'tours': tours})


@staff_requerido
def tour_crear(request):
    if request.method == 'POST':
        form = TourForm(request.POST, request.FILES)  # request.FILES: imagen
        if form.is_valid():
            tour = form.save()
            messages.success(request, f'Tour {tour.codigo} creado correctamente.')
            return redirect('tours:gestion')
        messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = TourForm()
    return render(request, 'tours/form.html', {'form': form, 'titulo': 'Nuevo tour / expedición'})


@staff_requerido
def tour_editar(request, slug):
    tour = get_object_or_404(TourExpedicion, slug=slug)
    if request.method == 'POST':
        form = TourForm(request.POST, request.FILES, instance=tour)
        if form.is_valid():
            form.save()
            messages.success(request, f'Tour {tour.codigo} actualizado.')
            return redirect('tours:gestion')
        messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = TourForm(instance=tour)  # formulario precargado
    return render(request, 'tours/form.html', {'form': form, 'titulo': f'Editar {tour.codigo}', 'tour': tour})


@staff_requerido
def tour_eliminar(request, slug):
    """Baja lógica con pantalla de confirmación previa."""
    tour = get_object_or_404(TourExpedicion, slug=slug)
    if request.method == 'POST':
        tour.activo = False
        tour.save(update_fields=['activo', 'actualizado'])
        messages.warning(request, f'Tour {tour.codigo} dado de baja. Puedes reactivarlo cuando quieras.')
        return redirect('tours:gestion')
    return render(request, 'tours/confirmar_eliminar.html', {'tour': tour})


@staff_requerido
@require_POST
def tour_reactivar(request, slug):
    tour = get_object_or_404(TourExpedicion, slug=slug)
    tour.activo = True
    tour.save(update_fields=['activo', 'actualizado'])
    messages.success(request, f'Tour {tour.codigo} reactivado.')
    return redirect('tours:gestion')


# ===================== ITINERARIO (request.session) =====================
def _personas(request):
    try:
        return int(request.POST.get('personas', 1))
    except (TypeError, ValueError):
        return 0


def itinerario_ver(request):
    itin = Itinerario(request)
    items = itin.items()
    return render(request, 'tours/itinerario.html', {'items': items, 'totales': itin.totales(items)})


@require_POST
def itinerario_agregar(request, pk):
    tour = get_object_or_404(TourExpedicion.objects.select_related('region'), pk=pk, activo=True)
    ok, mensaje = Itinerario(request).agregar(tour, _personas(request))
    (messages.success if ok else messages.error)(request, mensaje)
    return redirect('tours:itinerario' if ok else 'tours:detalle', **({} if ok else {'slug': tour.slug}))


@require_POST
def itinerario_actualizar(request, pk):
    tour = get_object_or_404(TourExpedicion, pk=pk)
    ok, mensaje = Itinerario(request).actualizar(tour, _personas(request))
    (messages.success if ok else messages.error)(request, mensaje)
    return redirect('tours:itinerario')


@require_POST
def itinerario_quitar(request, pk):
    if Itinerario(request).quitar(pk):
        messages.info(request, 'Tour quitado del itinerario.')
    return redirect('tours:itinerario')


@require_POST
def itinerario_vaciar(request):
    Itinerario(request).vaciar()
    messages.info(request, 'Itinerario vaciado.')
    return redirect('tours:itinerario')


@login_required
@require_POST
def itinerario_confirmar(request):
    """Genera un comprobante simulado y vacía la sesión (no modifica la BD)."""
    itin = Itinerario(request)
    items = itin.items()
    if not items:
        messages.warning(request, 'Tu itinerario está vacío.')
        return redirect('tours:catalogo')
    if any(i['excede_cupos'] for i in items):
        messages.error(request, 'Algunos tours ya no tienen cupos suficientes. Ajusta las cantidades.')
        return redirect('tours:itinerario')
    contexto = {
        'items': items,
        'totales': itin.totales(items),
        'codigo': f'ECO-{timezone.localdate():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}',
        'fecha': timezone.localtime(),
    }
    itin.vaciar()
    return render(request, 'tours/comprobante.html', contexto)
