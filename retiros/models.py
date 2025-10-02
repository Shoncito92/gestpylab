from django.db import models
from django.core.validators import MinLengthValidator

# Modelo para Zonas (predefinidas: las que mencionaste)
class Zona(models.Model):
    nombre = models.CharField(max_length=50, unique=True, help_text="Ej: Valparaíso, Viña del Mar")

    def __str__(self):
        return self.nombre

# Modelo para Solicitantes (agregamos dirección principal)
class Solicitante(models.Model):
    TIPO_SOLICITANTE = [
        ('medico', 'Médico Veterinario'),
        ('veterinaria', 'Veterinaria'),
        ('tecnico', 'Técnico Veterinario'),
    ]
    
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_SOLICITANTE, default='medico')
    telefono = models.CharField(max_length=20, validators=[MinLengthValidator(9)], help_text="Ej: +56 9 12345678")
    email = models.EmailField(unique=True, help_text="Importante: para enviar resultados")
    horarios_atencion = models.TextField(help_text="Ej: Lun-Vie 9:00-18:00")
    zona = models.ForeignKey(Zona, on_delete=models.CASCADE)
    direccion_principal = models.TextField(blank=True, help_text="Dirección fija del solicitante (opcional)")
    def __str__(self):
        return f"{self.nombre} ({self.tipo}) - {self.zona.nombre}"
    
# Modelo para Retiradores (fijos y complementarios)
class Retirador(models.Model):
    TIPO = [
        ('fijo', 'Retirador Fijo'),
        ('complementario', 'Complementario'),
    ]
    
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO, default='fijo')
    zonas_preferidas = models.ManyToManyField(Zona, help_text="Zonas que suele cubrir")

    def __str__(self):
        return self.nombre

# Modelo para Solicitudes de Retiro (agregamos lógica de dirección)
class SolicitudRetiro(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('asignado', 'Asignado'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]
    
    solicitante = models.ForeignKey(Solicitante, on_delete=models.CASCADE)
    usar_direccion_solicitante = models.BooleanField(default=True, help_text="¿Usar la dirección principal del solicitante?")
    direccion_retiro = models.TextField(help_text="Si no usas la del solicitante, pon la ubicación exacta aquí")
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    hora_solicitud = models.TimeField(auto_now_add=True)
    fecha_retiro = models.DateField(help_text="Hoy o mañana, según horario")
    retirador_asignado = models.ForeignKey(Retirador, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    notas = models.TextField(blank=True, help_text="Ej: Tipo de animal (canino, felino), urgencia")
    def save(self, *args, **kwargs):
        # Lógica automática: Si usas dirección del solicitante y tiene una, cópiala
        if self.usar_direccion_solicitante and self.solicitante.direccion_principal:
            self.direccion_retiro = self.solicitante.direccion_principal
        super().save(*args, **kwargs)
    def __str__(self):
        dir_str = self.direccion_retiro[:50] + "..." if len(self.direccion_retiro) > 50 else self.direccion_retiro
