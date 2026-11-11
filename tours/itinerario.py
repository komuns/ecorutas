"""Itinerario de viaje almacenado en request.session (sin persistir en la BD).

Estructura en sesión:  request.session['itinerario'] = {"<tour_id>": <n_personas>, ...}
Solo se guardan ids y cantidades; los precios se leen siempre desde la BD,
así el cliente no puede manipularlos.
"""
from .models import TourExpedicion

SESSION_KEY = 'itinerario'
TASA_AMBIENTAL_PCT = 5   # tasa de conservación de áreas protegidas
IVA_PCT = 19             # IVA Chile


def _porcentaje(valor, pct):
    """Porcentaje entero redondeado (half-up), en pesos chilenos."""
    return (valor * pct + 50) // 100


class Itinerario:
    def __init__(self, request):
        self.session = request.session
        self.datos = self.session.get(SESSION_KEY, {})

    # --- persistencia en sesión ---
    def _guardar(self):
        self.session[SESSION_KEY] = self.datos
        self.session.modified = True

    # --- operaciones ---
    def agregar(self, tour, personas):
        """Agrega un tour validando estado y cupos. Retorna (ok, mensaje)."""
        if personas < 1:
            return False, 'La cantidad de personas debe ser al menos 1.'
        if not tour.disponible:
            return False, f'«{tour.titulo}» no está disponible para reservar.'
        actuales = self.datos.get(str(tour.pk), 0)
        total = actuales + personas
        if total > tour.cupos:
            return False, f'Solo quedan {tour.cupos} cupos para «{tour.titulo}» (ya tienes {actuales} en tu itinerario).'
        self.datos[str(tour.pk)] = total
        self._guardar()
        return True, f'«{tour.titulo}» agregado al itinerario ({total} persona/s).'

    def actualizar(self, tour, personas):
        """Cambia la cantidad de personas de un tour ya agregado."""
        if str(tour.pk) not in self.datos:
            return False, 'Ese tour no está en tu itinerario.'
        if personas < 1:
            return False, 'La cantidad de personas debe ser al menos 1.'
        if personas > tour.cupos:
            return False, f'Solo quedan {tour.cupos} cupos para «{tour.titulo}».'
        self.datos[str(tour.pk)] = personas
        self._guardar()
        return True, f'Cantidad actualizada: {personas} persona/s en «{tour.titulo}».'

    def quitar(self, tour_id):
        if self.datos.pop(str(tour_id), None) is not None:
            self._guardar()
            return True
        return False

    def vaciar(self):
        self.datos = {}
        self.session.pop(SESSION_KEY, None)
        self.session.modified = True

    # --- consultas ---
    def __len__(self):
        """Cantidad de tours distintos (se usa en el contador del navbar)."""
        return len(self.datos)

    def items(self):
        """Lista de dicts con tour, personas y subtotal. Limpia tours que ya no existen."""
        ids = [int(i) for i in self.datos]
        tours = TourExpedicion.objects.filter(pk__in=ids, activo=True).select_related('region')
        resultado = []
        for tour in tours:
            personas = self.datos[str(tour.pk)]
            resultado.append({
                'tour': tour,
                'personas': personas,
                'subtotal': tour.tarifa_por_persona * personas,
                'excede_cupos': personas > tour.cupos or not tour.disponible,
            })
        # Eliminar de la sesión los tours dados de baja o borrados
        vigentes = {str(i['tour'].pk) for i in resultado}
        if set(self.datos) != vigentes:
            self.datos = {k: v for k, v in self.datos.items() if k in vigentes}
            self._guardar()
        return resultado

    def totales(self, items=None):
        """Desglose: subtotal, tasa ambiental, IVA y total final."""
        items = self.items() if items is None else items
        subtotal = sum(i['subtotal'] for i in items)
        tasa = _porcentaje(subtotal, TASA_AMBIENTAL_PCT)
        iva = _porcentaje(subtotal + tasa, IVA_PCT)
        return {
            'subtotal': subtotal,
            'tasa_ambiental': tasa,
            'iva': iva,
            'total': subtotal + tasa + iva,
            'personas': sum(i['personas'] for i in items),
            'tasa_pct': TASA_AMBIENTAL_PCT,
            'iva_pct': IVA_PCT,
        }
