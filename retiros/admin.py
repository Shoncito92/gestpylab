from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Zona, Solicitante, Retirador, SolicitudRetiro
import csv
from datetime import datetime

@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'total_solicitantes', 'total_retiradores']
    search_fields = ['nombre']
    ordering = ['nombre']
    
    def total_solicitantes(self, obj):
        """Muestra el total de solicitantes en esta zona"""
        count = obj.solicitante_set.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    total_solicitantes.short_description = 'Total Solicitantes'
    
    def total_retiradores(self, obj):
        """Muestra el total de retiradores que cubren esta zona"""
        count = obj.retirador_set.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    total_retiradores.short_description = 'Total Retiradores'

@admin.register(Solicitante)
class SolicitanteAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 
        'tipo', 
        'zona',
        'estado_email',
        'estado_direccion',
        'estado_horario',
        'datos_completos_badge',
        'total_solicitudes'
    ]
    list_filter = [
        'tipo', 
        'zona',
        'email_desconocido',
        'direccion_desconocida'
    ]
    search_fields = ['nombre', 'email', 'telefono', 'direccion_principal']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'tipo', 'zona', 'telefono'),
            'description': 'Datos principales del solicitante'
        }),
        ('Contacto - Email', {
            'fields': ('email', 'email_desconocido'),
            'description': 'Si el email es desconocido, marque la casilla y deje el campo vacío'
        }),
        ('Dirección', {
            'fields': ('direccion_principal', 'direccion_desconocida'),
            'description': 'Si la dirección es desconocida, marque la casilla y deje el campo vacío'
        }),
        ('Horarios de Atención', {
            'fields': ('horario_atencion_inicio', 'horario_atencion_fin', 'comentarios_horario_retiro'),
            'description': 'Horarios opcionales. Use comentarios para notas especiales (ej: "Colación 15-16 hrs")',
            'classes': ('collapse',)
        }),
    )
    
    actions = ['exportar_datos_faltantes', 'marcar_email_desconocido', 'marcar_direccion_desconocida']
    
    def estado_email(self, obj):
        """Muestra el estado del email con iconos"""
        if obj.email_desconocido:
            return format_html('<span style="color: orange;">⚠️ Desconocido</span>')
        elif obj.email:
            return format_html('<span style="color: green;">✅ {}</span>', obj.email[:30])
        else:
            return format_html('<span style="color: red;">❌ Sin email</span>')
    estado_email.short_description = 'Email'
    
    def estado_direccion(self, obj):
        """Muestra el estado de la dirección con iconos"""
        if obj.direccion_desconocida:
            return format_html('<span style="color: orange;">⚠️ Desconocida</span>')
        elif obj.direccion_principal:
            return format_html('<span style="color: green;">✅ {}</span>', obj.direccion_principal[:30])
        else:
            return format_html('<span style="color: red;">❌ Sin dirección</span>')
    estado_direccion.short_description = 'Dirección'
    
    def estado_horario(self, obj):
        """Muestra el estado del horario"""
        if obj.horario_atencion_inicio and obj.horario_atencion_fin:
            return format_html('<span style="color: green;">✅ {}</span>', obj.horario_completo)
        elif obj.comentarios_horario_retiro:
            return format_html('<span style="color: blue;">📝 {}</span>', obj.comentarios_horario_retiro[:30])
        else:
            return format_html('<span style="color: gray;">⏰ No especificado</span>')
    estado_horario.short_description = 'Horario'
    
    def datos_completos_badge(self, obj):
        """Badge que indica si los datos están completos"""
        if obj.tiene_datos_completos:
            return format_html('<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px;">✓ Completo</span>')
        else:
            return format_html('<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px;">⚠ Incompleto</span>')
    datos_completos_badge.short_description = 'Estado'
    
    def total_solicitudes(self, obj):
        """Muestra el total de solicitudes del solicitante"""
        count = obj.solicitudretiro_set.count()
        if count > 0:
            url = reverse('admin:retiros_solicitudretiro_changelist') + f'?solicitante__id__exact={obj.id}'
            return format_html('<a href="{}" style="font-weight: bold;">{} solicitudes</a>', url, count)
        return format_html('<span style="color: gray;">0 solicitudes</span>')
    total_solicitudes.short_description = 'Solicitudes'
    
    def exportar_datos_faltantes(self, request, queryset):
        """Exporta solicitantes con datos faltantes a CSV"""
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="solicitantes_datos_faltantes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        response.write('\ufeff')  # BOM para Excel
        
        writer = csv.writer(response)
        writer.writerow(['Nombre', 'Tipo', 'Zona', 'Teléfono', 'Email Faltante', 'Dirección Faltante', 'Horario'])
        
        for solicitante in queryset:
            if not solicitante.tiene_datos_completos:
                writer.writerow([
                    solicitante.nombre,
                    solicitante.get_tipo_display(),
                    solicitante.zona.nombre,
                    solicitante.telefono,
                    'SÍ' if solicitante.email_desconocido else 'NO',
                    'SÍ' if solicitante.direccion_desconocida else 'NO',
                    solicitante.horario_completo
                ])
        
        self.message_user(request, f'Se exportaron {queryset.filter(email_desconocido=True).count() + queryset.filter(direccion_desconocida=True).count()} solicitantes con datos faltantes.')
        return response
    exportar_datos_faltantes.short_description = '📥 Exportar datos faltantes a CSV'
    
    def marcar_email_desconocido(self, request, queryset):
        """Marca los emails como desconocidos"""
        updated = queryset.update(email_desconocido=True, email=None)
        self.message_user(request, f'{updated} solicitante(s) marcado(s) con email desconocido.')
    marcar_email_desconocido.short_description = '📧 Marcar email como desconocido'
    
    def marcar_direccion_desconocida(self, request, queryset):
        """Marca las direcciones como desconocidas"""
        updated = queryset.update(direccion_desconocida=True, direccion_principal='')
        self.message_user(request, f'{updated} solicitante(s) marcado(s) con dirección desconocida.')
    marcar_direccion_desconocida.short_description = '📍 Marcar dirección como desconocida'
    
    class Media:
        js = ('admin/js/solicitante_admin.js',)
        css = {
            'all': ('admin/css/solicitante_admin.css',)
        }

@admin.register(Retirador)
class RetiradorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'zonas_display', 'total_solicitudes_hoy']
    list_filter = ['tipo']
    search_fields = ['nombre']
    filter_horizontal = ['zonas_preferidas']
    ordering = ['nombre']
    
    def zonas_display(self, obj):
        """Muestra las zonas del retirador"""
        zonas = obj.zonas_preferidas.all()
        if zonas:
            return format_html(', '.join([f'<span style="background-color: #007bff; color: white; padding: 2px 6px; border-radius: 3px; margin: 2px;">{z.nombre}</span>' for z in zonas]))
        return format_html('<span style="color: gray;">Sin zonas asignadas</span>')
    zonas_display.short_description = 'Zonas'
    
    def total_solicitudes_hoy(self, obj):
        """Muestra el total de solicitudes del día"""
        from django.utils import timezone
        hoy = timezone.now().date()
        count = obj.solicitudretiro_set.filter(fecha_retiro=hoy, estado__in=['pendiente', 'asignado']).count()
        if count > 0:
            return format_html('<span style="background-color: #ffc107; color: black; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{} hoy</span>', count)
        return format_html('<span style="color: gray;">0 hoy</span>')
    total_solicitudes_hoy.short_description = 'Solicitudes Hoy'

@admin.register(SolicitudRetiro)
class SolicitudRetiroAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'solicitante_info',
        'direccion_corta',
        'fecha_retiro',
        'estado_badge',
        'retirador_info',
        'fecha_solicitud'
    ]
    list_filter = [
        'estado',
        'fecha_retiro',
        'retirador_asignado',
        'solicitante__zona',
        'solicitante__tipo'
    ]
    search_fields = [
        'solicitante__nombre',
        'direccion_retiro',
        'notas',
        'retirador_asignado__nombre'
    ]
    date_hierarchy = 'fecha_retiro'
    readonly_fields = ['fecha_solicitud', 'hora_solicitud']
    ordering = ['-fecha_retiro', '-hora_solicitud']
    
    fieldsets = (
        ('Solicitante', {
            'fields': ('solicitante',)
        }),
        ('Dirección de Retiro', {
            'fields': ('usar_direccion_solicitante', 'direccion_retiro'),
            'description': 'Si usa la dirección del solicitante, se copiará automáticamente'
        }),
        ('Programación', {
            'fields': ('fecha_retiro', 'fecha_solicitud', 'hora_solicitud'),
        }),
        ('Asignación', {
            'fields': ('retirador_asignado', 'estado'),
        }),
        ('Información Adicional', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marcar_completado', 'marcar_cancelado', 'reasignar_retirador']
    
    def solicitante_info(self, obj):
        """Muestra información del solicitante con link"""
        url = reverse('admin:retiros_solicitante_change', args=[obj.solicitante.id])
        return format_html(
            '<a href="{}" style="font-weight: bold;">{}</a><br>'
            '<small style="color: gray;">{} | {}</small>',
            url,
            obj.solicitante.nombre,
            obj.solicitante.get_tipo_display(),
            obj.solicitante.zona.nombre
        )
    solicitante_info.short_description = 'Solicitante'
    
    def direccion_corta(self, obj):
        """Muestra la dirección truncada"""
        if len(obj.direccion_retiro) > 50:
            return format_html('<span title="{}">{}</span>', obj.direccion_retiro, obj.direccion_retiro[:50] + '...')
        return obj.direccion_retiro
    direccion_corta.short_description = 'Dirección'
    
    def estado_badge(self, obj):
        """Badge colorido para el estado"""
        colors = {
            'pendiente': '#ffc107',
            'asignado': '#17a2b8',
            'completado': '#28a745',
            'cancelado': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">{}</span>',
            colors.get(obj.estado, '#6c757d'),
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def retirador_info(self, obj):
        """Muestra información del retirador"""
        if obj.retirador_asignado:
            url = reverse('admin:retiros_retirador_change', args=[obj.retirador_asignado.id])
            return format_html('<a href="{}" style="font-weight: bold;">{}</a>', url, obj.retirador_asignado.nombre)
        return format_html('<span style="color: orange;">⚠️ Sin asignar</span>')
    retirador_info.short_description = 'Retirador'
    
    def marcar_completado(self, request, queryset):
        """Marca solicitudes como completadas"""
        updated = queryset.update(estado='completado')
        self.message_user(request, f'{updated} solicitud(es) marcada(s) como completada(s).')
    marcar_completado.short_description = '✅ Marcar como completado'
    
    def marcar_cancelado(self, request, queryset):
        """Marca solicitudes como canceladas"""
        updated = queryset.update(estado='cancelado')
        self.message_user(request, f'{updated} solicitud(es) marcada(s) como cancelada(s).')
    marcar_cancelado.short_description = '❌ Marcar como cancelado'
    
    def reasignar_retirador(self, request, queryset):
        """Permite reasignar retiradores (requiere implementación adicional)"""
        self.message_user(request, 'Funcionalidad de reasignación en desarrollo.')
    reasignar_retirador.short_description = '🔄 Reasignar retirador'

# Personalización del sitio admin
admin.site.site_header = "GestPyLab - Administración"
admin.site.site_title = "GestPyLab Admin"
admin.site.index_title = "Panel de Control - Sistema de Retiros"
