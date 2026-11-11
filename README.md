# EcoRutas Chile

## Ficha de Registro de la Propuesta

- **Nombre de la Organización o Plataforma:** EcoRutas Chile
- **Modelo de Negocio / Giro:** Agencia de ecoturismo y rutas de aventura
- **Integrantes del Equipo:** [Cristobal Maximiliano Zurita Quiroz - 22113934-8]
- **Entidad de Contexto / Agrupación (ORM):** `RegionTuristica`
- **Entidad Principal Gestionable (ORM):** `TourExpedicion`
- **Propósito de la Sesión (request.session):** Itinerario de viaje: selección de tours por grupo (con control de cupos) y cálculo de tasa ambiental (5%) e IVA (19%).

## Funcionalidades

| Módulo | Qué incluye |
|---|---|
| Catálogo público | Tarjetas Bootstrap, búsqueda con `Q` (título, código, descripción), filtro por región, ordenamiento, `Paginator`, detalle por slug |
| Itinerario (sesión) | Agregar con validación de cupos, modificar personas, quitar, vaciar, desglose (subtotal, tasa, IVA, total), contador en el navbar (context processor), comprobante simulado |
| Backoffice | CRUD con `ModelForm` + imágenes, validaciones `clean_*`, baja lógica con confirmación, solo `is_staff` |
| Django Admin | Títulos corporativos, `list_display`, `list_filter`, `search_fields`, `list_editable`, `fieldsets`, acciones masivas |
| Seguridad | Registro, login, logout (POST), `Perfil` (RUT validado, teléfono, rol), `@login_required` + `@user_passes_test`, CSRF |

## Instalación paso a paso

```bash
# 1. Entorno virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Dependencias
pip install -r requirements.txt

# 3. Variables de entorno
cp .env.example .env             # Windows: copy .env.example .env

# 4. Migraciones (generar y aplicar)
python manage.py makemigrations accounts tours
python manage.py migrate

# 5. Datos de ejemplo (4 regiones, 8 tours con imagen, 2 usuarios)
python manage.py poblar_datos

# 6. Ejecutar
python manage.py runserver
```

Abrir http://127.0.0.1:8000/ (sitio) y http://127.0.0.1:8000/admin/ (administrador).

## Credenciales de prueba

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin12345` | Staff + superusuario (backoffice y Django Admin) |
| `cliente` | `cliente12345` | Usuario estándar (sin acceso a gestión) |

## Estructura

```
config/     settings (python-dotenv), urls
accounts/   Perfil, registro, validador de RUT, admin de usuarios
tours/      modelos, admin, forms, vistas, itinerario.py (sesión), context_processors.py,
            management/commands/poblar_datos.py
templates/  base.html + tours/ + registration/
static/     css/estilos.css
```

## Bitácora de Prompts de IA

Herramienta utilizada: Claude (Anthropic). La IA generó la base del proyecto a partir del PDF de la evaluación; yo revisé, probé y adapté el resultado. A continuación documento tres casos.

### Caso 1 - Arquitectura y modelado ORM
- **Prompt:** Adjunté el PDF de la evaluación y pedí: "Hazme el trabajo que cumpla con la rúbrica y el PDF; el tema que escogí es Agencia de Ecoturismo y Rutas".
- **Respuesta técnica:** La IA propuso dos apps (`accounts` y `tours`) y los modelos `RegionTuristica` (entidad de contexto) y `TourExpedicion` (entidad principal), unidos con `ForeignKey(on_delete=PROTECT)`. Incluyó `MinValueValidator(0)` en tarifa y cupos, `TextChoices` para dificultad y estado, `ImageField` y el campo `activo` para la baja lógica.
- **Adaptación y justificación crítica:** Verifiqué cada requisito del Módulo 1 del PDF contra el código. Entendí que `PROTECT` evita borrar una región que tenga tours (con `CASCADE` se perderían todos). La IA no ejecutó el proyecto, así que lo probé yo: las imágenes de las tarjetas del catálogo se veían cortadas y lo corregí con `aspect-ratio` en el CSS; además, los comandos de instalación estaban pensados para Linux y los adapté a PowerShell de Windows.

### Caso 2 - Consultas y manejo de sesión
- **Prompt:** Pedí ayuda para explicar el proyecto, la página y el código al profesor, y para prepararme ante las preguntas que pudiera hacer.
- **Respuesta técnica:** La IA explicó que el catálogo usa `select_related('region')` para traer la región junto con cada tour en una sola consulta y evitar el problema N+1. También explicó que el itinerario (`tours/itinerario.py`) guarda en `request.session` solo `{id: cantidad}` y lee precios y cupos desde la base de datos, de modo que el usuario no pueda manipular los valores.
- **Adaptación y justificación crítica:** Estudié `itinerario.py`, `views.py` y `models.py` para poder explicarlos con mis palabras. Entendí que si el precio se guardara en la sesión, un usuario podría alterarlo; por eso se consulta siempre la base de datos. Entendí también que el total se calcula como subtotal más tasa ambiental (5%) más IVA (19%) sobre el subtotal con tasa, y que esos porcentajes se pueden modificar en las constantes `TASA_AMBIENTAL_PCT` e `IVA_PCT`.

### Caso 3 - Seguridad y control de acceso
- **Prompt:** Consulté para qué sirven los Grupos del Django Admin y si se asocian a una cuenta cliente o admin.
- **Respuesta técnica:** La IA explicó que Django no distingue "cliente" y "admin" como tipos de cuenta: se diferencian por `is_staff` e `is_superuser`, y los grupos agrupan permisos que se asignan a cualquier usuario. También señaló que mi panel `/gestion/` solo comprueba `is_staff`, no los permisos del grupo.
- **Adaptación y justificación crítica:** Decidí mantener el control con `@login_required` y `@user_passes_test(es_staff)` porque cumple el requisito del PDF y es más simple de explicar. Reconozco como limitación que los grupos no restringen el panel `/gestion/`; podría resolverse con `@permission_required`. Un usuario autenticado sin permisos ve una página 403 propia, y el logout es un formulario POST con `{% csrf_token %}`.