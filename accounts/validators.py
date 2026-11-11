from django.core.exceptions import ValidationError


def normalizar_rut(valor):
    """Devuelve el RUT en formato 12345678-K (sin puntos, DV en mayúscula)."""
    limpio = valor.replace('.', '').replace('-', '').replace(' ', '').upper()
    if len(limpio) < 2:
        return limpio
    return f'{limpio[:-1]}-{limpio[-1]}'


def validar_rut(valor):
    """Valida un RUT chileno con el algoritmo módulo 11."""
    limpio = valor.replace('.', '').replace('-', '').replace(' ', '').upper()
    if len(limpio) < 8 or len(limpio) > 9:
        raise ValidationError('El RUT debe tener entre 7 y 8 dígitos más el dígito verificador.')
    cuerpo, dv = limpio[:-1], limpio[-1]
    if not cuerpo.isdigit():
        raise ValidationError('El cuerpo del RUT solo puede contener números.')
    suma, multiplicador = 0, 2
    for digito in reversed(cuerpo):
        suma += int(digito) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 7 else 2
    resto = 11 - (suma % 11)
    esperado = '0' if resto == 11 else 'K' if resto == 10 else str(resto)
    if dv != esperado:
        raise ValidationError('El dígito verificador del RUT no es válido.')
