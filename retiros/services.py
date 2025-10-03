"""
Servicios de lógica de negocio para GestPyLab
Separa la lógica de negocio de las vistas
"""
from django.db.models import Q
from django.utils import timezone
from .models import SolicitudRetiro, Retirador, Solicitante, Zona
import logging

logger = logging.getLogger(__name__)


class SolicitudService:
    """Servicio para manejar la lógica de negocio de solicitudes"""
    
    @staticmethod
    def asignar_retirador_automatico(solicitud):
        """
        Asigna automáticamente un retirador a una solicitud basándose en la zona.
        
        Args:
            solicitud: Objeto SolicitudRetiro
            
        Returns:
            tuple: (retirador_asignado, mensaje)
        """
        try:
            if solicitud.retirador_asignado:
                return solicitud.retirador_asignado, "Ya tiene retirador asignado"
            
            zona = solicitud.solicitante.zona
            
            # Buscar retiradores fijos en la zona
            retiradores = Retirador.objects.filter(
                zonas_preferidas=zona,
                tipo='fijo'
            ).prefetch_related('zonas_preferidas')
            
            if retiradores.exists():
                retirador = retiradores.first()
                solicitud.retirador_asignado = retirador
                solicitud.estado = 'asignado'
                solicitud.save()
                
                logger.info(f"Retirador {retirador.nombre} asignado a solicitud {solicitud.id}")
                return retirador, f"Asignado a {retirador.nombre}"
            else:
                logger.warning(f"No hay retiradores disponibles en zona {zona.nombre}")
                return None, f"No hay retiradores disponibles en la zona {zona.nombre}"
                
        except Exception as e:
            logger.error(f"Error al asignar retirador: {str(e)}")
            return None, f"Error al asignar retirador: {str(e)}"
    
    @staticmethod
    def obtener_pendientes_del_dia(fecha=None):
        """
        Obtiene todas las solicitudes pendientes de una fecha específica.
        
        Args:
            fecha: Fecha a consultar (por defecto hoy)
            
        Returns:
            QuerySet de SolicitudRetiro
        """
        if fecha is None:
            fecha = timezone.now().date()
        
        return SolicitudRetiro.objects.filter(
            Q(fecha_retiro=fecha) & Q(estado__in=['pendiente', 'asignado'])
        ).select_related(
            'solicitante',
            'solicitante__zona',
            'retirador_asignado'
        ).order_by('retirador_asignado', 'hora_solicitud')
    
    @staticmethod
    def obtener_solicitudes_retirador(retirador, fecha=None):
        """
        Obtiene las solicitudes asignadas a un retirador específico.
        
        Args:
            retirador: Objeto Retirador
            fecha: Fecha a consultar (por defecto hoy)
            
        Returns:
            QuerySet de SolicitudRetiro
        """
        if fecha is None:
            fecha = timezone.now().date()
        
        return SolicitudRetiro.objects.filter(
            Q(fecha_retiro=fecha) & (
                Q(retirador_asignado=retirador) | 
                Q(retirador_asignado__isnull=True, 
                  solicitante__zona__in=retirador.zonas_preferidas.all())
            ) & Q(estado__in=['pendiente', 'asignado'])
        ).select_related(
            'solicitante',
            'solicitante__zona',
            'retirador_asignado'
        ).order_by('hora_solicitud')
    
    @staticmethod
    def marcar_como_completado(solicitud_id):
        """
        Marca una solicitud como completada.
        
        Args:
            solicitud_id: ID de la solicitud
            
        Returns:
            tuple: (success, mensaje, solicitud)
        """
        try:
            solicitud = SolicitudRetiro.objects.get(id=solicitud_id)
            solicitud.estado = 'completado'
            solicitud.save()
            
            logger.info(f"Solicitud {solicitud_id} marcada como completada")
            return True, f"Solicitud de {solicitud.solicitante.nombre} completada", solicitud
            
        except SolicitudRetiro.DoesNotExist:
            logger.error(f"Solicitud {solicitud_id} no encontrada")
            return False, "Solicitud no encontrada", None
        except Exception as e:
            logger.error(f"Error al marcar solicitud {solicitud_id} como completada: {str(e)}")
            return False, f"Error: {str(e)}", None
    
    @staticmethod
    def validar_solicitud(solicitud_data):
        """
        Valida los datos de una solicitud antes de crearla.
        
        Args:
            solicitud_data: Diccionario con datos de la solicitud
            
        Returns:
            tuple: (es_valido, errores)
        """
        errores = []
        
        # Validar solicitante
        if not solicitud_data.get('solicitante'):
            errores.append("Debe seleccionar un solicitante")
        
        # Validar dirección
        if not solicitud_data.get('direccion_retiro'):
            errores.append("Debe proporcionar una dirección de retiro")
        
        # Validar fecha
        if not solicitud_data.get('fecha_retiro'):
            errores.append("Debe seleccionar una fecha de retiro")
        
        # Validar horario (11:00 - 14:00)
        now = timezone.now().time()
        hora_inicio = timezone.datetime.strptime('11:00', '%H:%M').time()
        hora_fin = timezone.datetime.strptime('14:00', '%H:%M').time()
        
        if not (hora_inicio <= now <= hora_fin):
            errores.append("Solo se pueden crear solicitudes entre 11:00 y 14:00 hrs")
        
        return len(errores) == 0, errores


class SolicitanteService:
    """Servicio para manejar la lógica de negocio de solicitantes"""
    
    @staticmethod
    def obtener_solicitantes_incompletos():
        """
        Obtiene todos los solicitantes con datos incompletos.
        
        Returns:
            QuerySet de Solicitante
        """
        return Solicitante.objects.filter(
            Q(email_desconocido=True) | Q(direccion_desconocida=True)
        ).select_related('zona')
    
    @staticmethod
    def buscar_solicitantes(query):
        """
        Busca solicitantes por nombre, email, teléfono o dirección.
        
        Args:
            query: Texto de búsqueda
            
        Returns:
            QuerySet de Solicitante
        """
        if not query or len(query) < 2:
            return Solicitante.objects.none()
        
        return Solicitante.objects.filter(
            Q(nombre__icontains=query) |
            Q(email__icontains=query) |
            Q(telefono__icontains=query) |
            Q(direccion_principal__icontains=query)
        ).select_related('zona')[:10]  # Limitar a 10 resultados
    
    @staticmethod
    def validar_datos_solicitante(solicitante):
        """
        Valida que un solicitante tenga todos los datos necesarios.
        
        Args:
            solicitante: Objeto Solicitante
            
        Returns:
            tuple: (es_valido, datos_faltantes)
        """
        datos_faltantes = []
        
        if solicitante.email_desconocido or not solicitante.email:
            datos_faltantes.append('email')
        
        if solicitante.direccion_desconocida or not solicitante.direccion_principal:
            datos_faltantes.append('dirección')
        
        if not solicitante.telefono:
            datos_faltantes.append('teléfono')
        
        return len(datos_faltantes) == 0, datos_faltantes


class EstadisticasService:
    """Servicio para generar estadísticas del sistema"""
    
    @staticmethod
    def obtener_resumen_dashboard(fecha=None):
        """
        Obtiene el resumen de estadísticas para el dashboard.
        
        Args:
            fecha: Fecha a consultar (por defecto hoy)
            
        Returns:
            dict con estadísticas
        """
        if fecha is None:
            fecha = timezone.now().date()
        
        # Total pendientes del día
        total_pendientes = SolicitudRetiro.objects.filter(
            Q(fecha_retiro=fecha) & Q(estado__in=['pendiente', 'asignado'])
        ).count()
        
        # Total solicitantes
        total_solicitantes = Solicitante.objects.count()
        
        # Solicitantes con datos incompletos
        solicitantes_incompletos = Solicitante.objects.filter(
            Q(email_desconocido=True) | Q(direccion_desconocida=True)
        ).count()
        
        # Resumen por retirador
        retiradores = Retirador.objects.prefetch_related('zonas_preferidas').all()
        solicitudes_hoy = SolicitudRetiro.objects.filter(
            Q(fecha_retiro=fecha) & Q(estado__in=['pendiente', 'asignado'])
        ).select_related('solicitante', 'solicitante__zona', 'retirador_asignado')
        
        resumenes_retiradores = []
        for retirador in retiradores:
            zonas_ids = [z.id for z in retirador.zonas_preferidas.all()]
            count = sum(
                1 for s in solicitudes_hoy 
                if s.retirador_asignado == retirador or 
                (s.retirador_asignado is None and s.solicitante.zona_id in zonas_ids)
            )
            resumenes_retiradores.append({
                'retirador': retirador,
                'count': count
            })
        
        return {
            'total_pendientes': total_pendientes,
            'total_solicitantes': total_solicitantes,
            'solicitantes_incompletos': solicitantes_incompletos,
            'resumenes_retiradores': resumenes_retiradores,
            'fecha': fecha
        }
    
    @staticmethod
    def obtener_estadisticas_zona(zona_id):
        """
        Obtiene estadísticas de una zona específica.
        
        Args:
            zona_id: ID de la zona
            
        Returns:
            dict con estadísticas de la zona
        """
        try:
            zona = Zona.objects.get(id=zona_id)
            
            total_solicitantes = Solicitante.objects.filter(zona=zona).count()
            total_retiradores = Retirador.objects.filter(zonas_preferidas=zona).count()
            
            hoy = timezone.now().date()
            solicitudes_hoy = SolicitudRetiro.objects.filter(
                solicitante__zona=zona,
                fecha_retiro=hoy
            ).count()
            
            return {
                'zona': zona,
                'total_solicitantes': total_solicitantes,
                'total_retiradores': total_retiradores,
                'solicitudes_hoy': solicitudes_hoy
            }
        except Zona.DoesNotExist:
            return None
