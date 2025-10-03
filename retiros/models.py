from django.db import models
from django.core.validators import MinLengthValidator

# Modelo para Zonas (predefinidas: las que mencionaste)
class Zona(models.Model):
    nombre = models.CharField(max_length=50, unique=True, help_text="Ej: Valparaíso, Viña del Mar")

    def __str__(self):
        return self.nombre

# Modelo para Solicitantes (mejorado con campos opcionales y validaciones)
class Solicitante(models.Model):
    TIPO_SOLICITANTE = [
        ('medico', 'Médico Veterinario'),
        ('veterinaria', 'Veterinaria'),
        ('tecnico', 'Técnico Veterinario'),
        ('ayudante', 'Ayudante Veterinario'),
        ('tutor', 'Tutor/Dueño de Mascota'),
    ]
    
    nombre = models.CharField(max_length=100, help_text="Nombre completo del solicitante")
    tipo = models.CharField(max_length=20, choices=TIPO_SOLICITANTE, default='medico')
    telefono = models.CharField(max_length=20, validators=[MinLengthValidator(9)], help_text="Ej: +56 9 12345678")
    
    # Email opcional con flag de desconocido
    email = models.EmailField(
        blank=True, 
        null=True,
        help_text="Email para enviar resultados (opcional si se marca como desconocido)"
    )
    email_desconocido = models.BooleanField(
        default=False, 
        help_text="Marque si el email no se conoce aún"
    )
    
    # Horarios opcionales y flexibles
    horario_atencion_inicio = models.TimeField(
        blank=True, 
        null=True,
        help_text="Hora de inicio de atención (opcional)"
    )
    horario_atencion_fin = models.TimeField(
        blank=True, 
        null=True,
        help_text="Hora de fin de atención (opcional)"
    )
    comentarios_horario_retiro = models.TextField(
        blank=True,
        help_text="Comentarios especiales sobre horarios (ej: 'Desde las 12:00 pm', 'Colación 15-16 hrs')"
    )
    
    zona = models.ForeignKey(Zona, on_delete=models.CASCADE)
    
    # Dirección opcional con flag de desconocida
    direccion_principal = models.TextField(
        blank=True,
        help_text="Dirección fija del solicitante (opcional si se marca como desconocida)"
    )
    direccion_desconocida = models.BooleanField(
        default=False,
        help_text="Marque si la dirección no se conoce aún"
    )
    
    class Meta:
        verbose_name = "Solicitante"
        verbose_name_plural = "Solicitantes"
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['nombre']),
            models.Index(fields=['tipo']),
            models.Index(fields=['zona']),
        ]
    
    def clean(self):
        """Validación personalizada para campos condicionales"""
        from django.core.exceptions import ValidationError
        
        # Si email no está marcado como desconocido, debe tener un valor
        if not self.email_desconocido and not self.email:
            raise ValidationError({
                'email': 'Debe proporcionar un email o marcar como desconocido.'
            })
        
        # Si email está marcado como desconocido, no debe tener valor
        if self.email_desconocido and self.email:
            raise ValidationError({
                'email': 'No puede tener email si está marcado como desconocido.'
            })
        
        # Validar que si hay hora de inicio, también haya hora de fin
        if self.horario_atencion_inicio and not self.horario_atencion_fin:
            raise ValidationError({
                'horario_atencion_fin': 'Debe especificar hora de fin si hay hora de inicio.'
            })
        
        if self.horario_atencion_fin and not self.horario_atencion_inicio:
            raise ValidationError({
                'horario_atencion_inicio': 'Debe especificar hora de inicio si hay hora de fin.'
            })
    
    def save(self, *args, **kwargs):
        """Override save para ejecutar validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()}) - {self.zona.nombre}"
    
    @property
    def horario_completo(self):
        """Retorna el horario completo formateado"""
        if self.horario_atencion_inicio and self.horario_atencion_fin:
            horario = f"{self.horario_atencion_inicio.strftime('%H:%M')} - {self.horario_atencion_fin.strftime('%H:%M')}"
            if self.comentarios_horario_retiro:
                horario += f" ({self.comentarios_horario_retiro})"
            return horario
        elif self.comentarios_horario_retiro:
            return self.comentarios_horario_retiro
        return "Horario no especificado"
    
    @property
    def tiene_datos_completos(self):
        """Verifica si el solicitante tiene todos los datos necesarios"""
        return (
            (self.email or self.email_desconocido) and
            (self.direccion_principal or self.direccion_desconocida)
        )
    
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
