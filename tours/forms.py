from django import forms
from django.core.exceptions import ValidationError

from .models import TourExpedicion


class TourForm(forms.ModelForm):
    """Formulario de creación/edición de tours con estilos Bootstrap 5."""

    class Meta:
        model = TourExpedicion
        fields = [
            'region', 'codigo', 'titulo', 'descripcion', 'punto_encuentro', 'requisitos',
            'tarifa_por_persona', 'cupos', 'duracion_dias', 'fecha_salida',
            'dificultad', 'estado', 'imagen', 'activo',
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'requisitos': forms.Textarea(attrs={'rows': 3}),
            'fecha_salida': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            if isinstance(campo.widget, forms.CheckboxInput):
                clase = 'form-check-input'
            elif isinstance(campo.widget, forms.Select):
                clase = 'form-select'
            else:
                clase = 'form-control'
            campo.widget.attrs['class'] = clase

    def clean_codigo(self):
        codigo = self.cleaned_data['codigo'].strip().upper()
        existe = TourExpedicion.objects.filter(codigo__iexact=codigo).exclude(pk=self.instance.pk).exists()
        if existe:
            raise ValidationError(f'Ya existe un tour con el código {codigo}.')
        return codigo

    def clean_tarifa_por_persona(self):
        tarifa = self.cleaned_data['tarifa_por_persona']
        if tarifa < 0:
            raise ValidationError('La tarifa no puede ser negativa.')
        return tarifa

    def clean_cupos(self):
        cupos = self.cleaned_data['cupos']
        if cupos < 0:
            raise ValidationError('Los cupos no pueden ser negativos.')
        return cupos
