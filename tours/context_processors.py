from .itinerario import SESSION_KEY


def itinerario_global(request):
    """Inyecta en todas las plantillas la cantidad de tours del itinerario (Navbar)."""
    return {'itinerario_count': len(request.session.get(SESSION_KEY, {}))}
