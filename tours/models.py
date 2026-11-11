from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class RegionTuristica(models.Model):
    """Entidad de contexto: agrupa los tours por región geográfica."""

    nombre = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)
    descripcion = models.TextField('descripción', blank=True)
    clima = models.CharField(max_length=120, blank=True)
    temporada_recomendada = models.CharField('temporada recomendada', max_length=120, blank=True)

    class Meta:
        verbose_name = 'región turística'
        verbose_name_plural = 'regiones turísticas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)


class TourExpedicion(models.Model):
    """Entidad principal gestionable: un tour o expedición del catálogo."""

    class Dificultad(models.TextChoices):
        FACIL = 'FACIL', 'Fácil'
        MODERADA = 'MODERADA', 'Moderada'
        DIFICIL = 'DIFICIL', 'Difícil'
        EXTREMA = 'EXTREMA', 'Extrema'

    class Estado(models.TextChoices):
        DISPONIBLE = 'DISPONIBLE', 'Disponible'
        EN_CURSO = 'EN_CURSO', 'En curso'
        AGOTADO = 'AGOTADO', 'Agotado'
        SUSPENDIDO = 'SUSPENDIDO', 'Suspendido'

    # Relación referencial: PROTECT impide borrar una región que tenga tours.
    region = models.ForeignKey(
        RegionTuristica, on_delete=models.PROTECT, related_name='tours', verbose_name='región'
    )
    # Identificación
    codigo = models.CharField(
        'código', max_length=10, unique=True,
        validators=[RegexValidator(r'^[A-Za-z]{3}-\d{3}$', 'Formato válido: ABC-123 (3 letras, guion y 3 números).')],
        help_text='Formato ABC-123. Debe ser único.',
    )
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    # Atributos descriptivos
    titulo = models.CharField('título', max_length=150)
    descripcion = models.TextField('descripción')
    punto_encuentro = models.CharField('punto de encuentro', max_length=150, blank=True)
    requisitos = models.TextField('equipo y requisitos', blank=True)
    # Atributos cuantitativos con validación (no admiten negativos)
    tarifa_por_persona = models.IntegerField(
        'tarifa por persona (CLP)', validators=[MinValueValidator(0)]
    )
    cupos = models.IntegerField('cupos disponibles', validators=[MinValueValidator(0)])
    duracion_dias = models.IntegerField('duración (días)', default=1, validators=[MinValueValidator(1)])
    fecha_salida = models.DateField('fecha de salida')
    # Opciones cerradas
    dificultad = models.CharField(max_length=10, choices=Dificultad.choices, default=Dificultad.MODERADA)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.DISPONIBLE)
    # Multimedia
    imagen = models.ImageField(upload_to='tours/', blank=True, null=True)
    # Baja lógica
    activo = models.BooleanField('vigente', default=True, help_text='Desmarcar para dar de baja sin borrar el registro.')
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'tour / expedición'
        verbose_name_plural = 'tours y expediciones'
        ordering = ['region__nombre', 'codigo']

    def __str__(self):
        return f'{self.codigo} · {self.titulo}'

    def get_absolute_url(self):
        return reverse('tours:detalle', kwargs={'slug': self.slug})

    @property
    def disponible(self):
        """True si se puede reservar: vigente, estado Disponible y con cupos."""
        return self.activo and self.estado == self.Estado.DISPONIBLE and self.cupos > 0

    def save(self, *args, **kwargs):
        self.codigo = self.codigo.upper()
        if not self.slug:
            base = slugify(f'{self.codigo}-{self.titulo}')[:110]
            slug, n = base, 2
            while TourExpedicion.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)
