from django.contrib import admin
from .models import Zona, Solicitante, Retirador, SolicitudRetiro

@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = ['nombre']
    search_fields = ['nombre']

@admin.register(Solicitante)
class SolicitanteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'email', 'zona', 'direccion_principal']
    list_filter = ['tipo', 'zona']
    search_fields = ['nombre', 'email']

@admin.register(Retirador)
class RetiradorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo']
    filter_horizontal = ['zonas_preferidas']  # Interfaz gráfica para asignar zonas

@admin.register(SolicitudRetiro)
class SolicitudRetiroAdmin(admin.ModelAdmin):
    list_display = ['solicitante', 'usar_direccion_solicitante', 'direccion_retiro', 'fecha_retiro', 'estado', 'retirador_asignado']
    list_filter = ['estado', 'fecha_retiro', 'retirador_asignado', 'solicitante__zona']
    search_fields = ['solicitante__nombre', 'direccion_retiro']
    date_hierarchy = 'fecha_retiro'  # Filtro por fecha
    readonly_fields = ['fecha_solicitud', 'hora_solicitud']
    fields = ['solicitante', 'usar_direccion_solicitante', 'direccion_retiro', 'fecha_retiro', 'retirador_asignado', 'estado', 'notas']