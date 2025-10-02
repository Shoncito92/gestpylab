from django import forms
from .models import SolicitudRetiro, Solicitante, Retirador
from django.utils import timezone
from datetime import datetime, timedelta

class SolicitudRetiroForm(forms.ModelForm):
    usar_direccion_solicitante = forms.BooleanField(required=False, initial=True, label="Usar dirección principal del solicitante (si aplica)")

    class Meta:
        model = SolicitudRetiro
        fields = ['solicitante', 'usar_direccion_solicitante', 'direccion_retiro', 'fecha_retiro', 'retirador_asignado', 'notas', 'estado']
        widgets = {
            'solicitante': forms.Select(attrs={'class': 'form-control'}),
            'direccion_retiro': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'fecha_retiro': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Autocompletado: Al elegir solicitante, podrías usar JS después, pero por ahora, el save maneja la dirección
        # Opciones para fecha_retiro: Hoy o mañana por defecto
        hoy = timezone.now().date()
        manana = hoy + timedelta(days=1)
        self.fields['fecha_retiro'].widget.attrs['value'] = hoy.strftime('%Y-%m-%d')  # Default hoy

    def clean_hora_solicitud(self):
        # Validación básica de horario (11-14); expandimos después
        now = timezone.now().time()
        if now.hour < 11 or now.hour > 14:
            raise forms.ValidationError("Solo se pueden agendar entre 11:00 y 14:00.")
        return now