"""python manage.py poblar_datos  ->  carga regiones, tours y usuarios de prueba.

Es idempotente: se puede ejecutar varias veces sin duplicar datos.
Las imágenes se generan con Pillow (degradados con el título) para no depender de internet.
"""
import unicodedata
from datetime import timedelta
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from accounts.models import Perfil
from tours.models import RegionTuristica, TourExpedicion

REGIONES = [
    {'nombre': 'Norte Grande', 'clima': 'Desértico, noches frías', 'temporada_recomendada': 'Todo el año',
     'descripcion': 'Desierto de Atacama: salares, géiseres, lagunas altiplánicas y los cielos más limpios del planeta.',
     'color': (196, 120, 52)},
    {'nombre': 'Zona Central', 'clima': 'Mediterráneo', 'temporada_recomendada': 'Septiembre a Abril',
     'descripcion': 'Valles, viñedos y cordillera de los Andes a pocas horas de Santiago.',
     'color': (120, 140, 70)},
    {'nombre': 'Lagos y Volcanes', 'clima': 'Templado lluvioso', 'temporada_recomendada': 'Diciembre a Marzo',
     'descripcion': 'Volcanes nevados, termas, lagos y bosque valdiviano en la zona sur.',
     'color': (40, 110, 90)},
    {'nombre': 'Patagonia Austral', 'clima': 'Frío y ventoso', 'temporada_recomendada': 'Noviembre a Marzo',
     'descripcion': 'Glaciares, fiordos y montañas icónicas como las Torres del Paine.',
     'color': (50, 90, 130)},
]

# (código, región, título, días, tarifa, cupos, dificultad, estado, salida en N días, punto de encuentro)
TOURS = [
    ('NOR-001', 'Norte Grande', 'Valle de la Luna y Astronomía en San Pedro de Atacama', 3, 189000, 12, 'FACIL', 'DISPONIBLE', 20,
     'Plaza de San Pedro de Atacama',
     'Recorrido por el Valle de la Luna, Valle de la Muerte y una noche de observación astronómica guiada con telescopios. Incluye traslados, guía bilingüe y snack de altura.',
     'Ropa abrigada para la noche, protector solar factor 50+, sombrero y 2 litros de agua por persona.'),
    ('NOR-002', 'Norte Grande', 'Géiseres del Tatio y Lagunas Altiplánicas', 2, 149000, 10, 'MODERADA', 'DISPONIBLE', 25,
     'Hotel base en San Pedro de Atacama',
     'Salida de madrugada a los Géiseres del Tatio, baño en termas naturales y visita a las lagunas Miscanti y Miñiques sobre los 4.000 msnm.',
     'Aclimatación previa recomendada. Traje de baño, toalla, ropa térmica y guantes.'),
    ('CEN-001', 'Zona Central', 'Trekking Glaciar El Morado, Cajón del Maipo', 1, 59000, 14, 'MODERADA', 'DISPONIBLE', 9,
     'Estación Baquedano, Metro Santiago',
     'Caminata de 8 km hasta el mirador del Glaciar El Morado con vistas al volcán San José. Almuerzo tipo picnic incluido.',
     'Zapatillas de trekking, bastones (opcionales), 1,5 litros de agua y cortaviento.'),
    ('CEN-002', 'Zona Central', 'Ruta del Vino en Bicicleta, Valle de Colchagua', 1, 79000, 16, 'FACIL', 'DISPONIBLE', 14,
     'Plaza de Armas de Santa Cruz',
     'Pedaleo suave entre viñedos con degustación en dos bodegas boutique y almuerzo campestre.',
     'Ropa cómoda, gorro y documento de identidad (degustación solo mayores de 18 años).'),
    ('SUR-001', 'Lagos y Volcanes', 'Ascenso al Volcán Villarrica', 1, 95000, 8, 'DIFICIL', 'DISPONIBLE', 12,
     'Oficina EcoRutas, Pucón',
     'Ascenso guiado hasta el cráter del volcán con equipo técnico completo y descenso deslizándose por la nieve.',
     'Buena condición física. Equipo técnico incluido; llevar ropa de montaña y lentes de sol.'),
    ('SUR-002', 'Lagos y Volcanes', 'Termas y Bosque Valdiviano en Huilo Huilo', 3, 210000, 6, 'FACIL', 'DISPONIBLE', 30,
     'Terminal de Buses de Panguipulli',
     'Tres días de senderos en la selva valdiviana, avistamiento de fauna nativa y termas bajo los árboles.',
     'Calzado impermeable, chaqueta de lluvia y repelente de insectos.'),
    ('PAT-001', 'Patagonia Austral', 'Circuito W, Torres del Paine', 5, 690000, 5, 'DIFICIL', 'DISPONIBLE', 45,
     'Puerto Natales, Terminal María Behety',
     'Cinco días recorriendo Valle Francés, Glaciar Grey y Base de las Torres con refugios y comidas incluidas.',
     'Experiencia previa en trekking, saco de dormir -5°C, ropa técnica por capas y bastones.'),
    ('PAT-002', 'Patagonia Austral', 'Navegación Glaciar Grey y Fiordos', 2, 320000, 0, 'MODERADA', 'SUSPENDIDO', 35,
     'Puerto Natales, muelle principal',
     'Navegación entre témpanos hasta el frente del glaciar con brindis con hielo milenario. Suspendido temporalmente por condiciones climáticas.',
     'Ropa impermeable y térmica, lentes de sol y cámara.'),
]

USUARIOS = [
    {'username': 'admin', 'password': 'admin12345', 'staff': True, 'super': True, 'rut': '11111111-1',
     'nombre': 'Administrador', 'apellido': 'EcoRutas', 'email': 'admin@ecorutas.cl', 'rol': Perfil.Rol.ADMINISTRATIVO},
    {'username': 'cliente', 'password': 'cliente12345', 'staff': False, 'super': False, 'rut': '22222222-2',
     'nombre': 'Camila', 'apellido': 'Rojas', 'email': 'cliente@ecorutas.cl', 'rol': Perfil.Rol.CLIENTE},
]


def generar_imagen(titulo, color):
    """Crea una imagen 800x520 con degradado vertical y el título."""
    ancho, alto = 800, 520
    img = Image.new('RGB', (ancho, alto))
    draw = ImageDraw.Draw(img)
    for y in range(alto):
        f = y / alto
        factor = 1.15 - 0.6 * f
        draw.line([(0, y), (ancho, y)], fill=tuple(min(255, int(c * factor)) for c in color))
    try:
        fuente = ImageFont.load_default(size=34)
    except TypeError:  # Pillow antiguo
        fuente = ImageFont.load_default()
    # Triángulos simulando montañas
    draw.polygon([(0, alto), (220, 300), (420, alto)], fill=(60, 85, 78))
    draw.polygon([(300, alto), (560, 240), (800, alto)], fill=(20, 40, 35))
    # Título en líneas de ~28 caracteres
    # La fuente por defecto de Pillow no dibuja tildes: se quitan solo en la imagen.
    titulo = unicodedata.normalize('NFKD', titulo).encode('ascii', 'ignore').decode()
    palabras, lineas, actual = titulo.split(), [], ''
    for p in palabras:
        if len(actual) + len(p) > 28:
            lineas.append(actual.strip())
            actual = ''
        actual += p + ' '
    lineas.append(actual.strip())
    y = 40
    for linea in lineas[:4]:
        draw.text((40, y), linea, fill='white', font=fuente)
        y += 46
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    return buffer.getvalue()


class Command(BaseCommand):
    help = 'Carga datos de ejemplo: regiones, tours y usuarios de prueba (admin y cliente).'

    def handle(self, *args, **options):
        regiones = {}
        for datos in REGIONES:
            color = datos.pop('color')
            region, _ = RegionTuristica.objects.update_or_create(nombre=datos['nombre'], defaults=datos)
            region._color = color
            regiones[region.nombre] = region
        self.stdout.write(self.style.SUCCESS(f'{len(regiones)} regiones turísticas listas.'))

        hoy = timezone.localdate()
        for (codigo, reg, titulo, dias, tarifa, cupos, dif, estado, salida, punto, desc, req) in TOURS:
            region = regiones[reg]
            tour, creado = TourExpedicion.objects.update_or_create(
                codigo=codigo,
                defaults={
                    'region': region, 'titulo': titulo, 'duracion_dias': dias,
                    'tarifa_por_persona': tarifa, 'cupos': cupos, 'dificultad': dif, 'estado': estado,
                    'fecha_salida': hoy + timedelta(days=salida), 'punto_encuentro': punto,
                    'descripcion': desc, 'requisitos': req, 'activo': True,
                },
            )
            if not tour.imagen:
                contenido = generar_imagen(titulo, region._color)
                tour.imagen.save(f'{codigo.lower()}.jpg', ContentFile(contenido), save=True)
        self.stdout.write(self.style.SUCCESS(f'{len(TOURS)} tours y expediciones listos.'))

        for u in USUARIOS:
            user, creado = User.objects.get_or_create(username=u['username'], defaults={
                'first_name': u['nombre'], 'last_name': u['apellido'], 'email': u['email'],
                'is_staff': u['staff'], 'is_superuser': u['super'],
            })
            if creado:
                user.set_password(u['password'])
                user.save()
            Perfil.objects.get_or_create(user=user, defaults={'rut': u['rut'], 'telefono': '+56912345678', 'rol': u['rol']})
        self.stdout.write(self.style.SUCCESS('Usuarios de prueba listos:'))
        self.stdout.write('  admin   / admin12345   (staff + superusuario)')
        self.stdout.write('  cliente / cliente12345 (usuario estándar)')
