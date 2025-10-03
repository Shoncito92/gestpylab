from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count, Prefetch
from django.http import JsonResponse
from .models import SolicitudRetiro, Retirador, Solicitante
from .forms import SolicitudRetiroForm
from .utils import generar_pdf_lista_retiros, enviar_notificacion_datos_faltantes
from django.utils import timezone
from datetime import timedelta
import logging

# Configurar logger
logger = logging.getLogger(__name__)

def agregar_solicitud(request):
    """
    Vista para agregar una nueva solicitud de retiro.
    Incluye asignación automática de retirador basada en zona.
    """
    try:
        if request.method == 'POST':
            form = SolicitudRetiroForm(request.POST)
            if form.is_valid():
                solicitud = form.save()
                
                # Lógica de asignación automática por zona
                if not solicitud.retirador_asignado:
                    zona = solicitud.solicitante.zona
                    # Optimizado: prefetch zonas para evitar queries adicionales
                    retiradores = Retirador.objects.filter(
                        zonas_preferidas=zona, 
                        tipo='fijo'
                    ).prefetch_related('zonas_preferidas')
                    
                    if retiradores.exists():
                        solicitud.retirador_asignado = retiradores.first()
                        solicitud.estado = 'asignado'
                        solicitud.save()
                        messages.success(
                            request, 
                            f'Solicitud agregada para {solicitud.solicitante.nombre}. '
                            f'Asignada a {solicitud.retirador_asignado}.'
                        )
                    else:
                        messages.warning(
                            request,
                            f'Solicitud agregada para {solicitud.solicitante.nombre}, '
                            f'pero no hay retiradores disponibles en la zona {zona.nombre}.'
                        )
                else:
                    messages.success(
                        request,
                        f'Solicitud agregada para {solicitud.solicitante.nombre}.'
                    )
                
                return redirect('lista_pendientes')
        else:
            form = SolicitudRetiroForm()
        
        return render(request, 'retiros/agregar_solicitud.html', {'form': form})
    
    except Exception as e:
        logger.error(f"Error al agregar solicitud: {str(e)}")
        messages.error(request, 'Ocurrió un error al agregar la solicitud. Por favor, intente nuevamente.')
        return redirect('home')

def lista_pendientes(request):
    """
    Vista optimizada para listar solicitudes pendientes del día.
    Usa select_related para reducir queries.
    """
    try:
        hoy = timezone.now().date()
        
        # Optimizado: select_related para evitar N+1 queries
        pendientes = SolicitudRetiro.objects.filter(
            Q(fecha_retiro=hoy) & Q(estado__in=['pendiente', 'asignado'])
        ).select_related(
            'solicitante',
            'solicitante__zona',
            'retirador_asignado'
        ).order_by('retirador_asignado', 'hora_solicitud')
        
        context = {
            'pendientes': pendientes,
            'hoy': hoy,
            'total': pendientes.count()
        }
        
        return render(request, 'retiros/lista_pendientes.html', context)
    
    except Exception as e:
        logger.error(f"Error al listar pendientes: {str(e)}")
        messages.error(request, 'Ocurrió un error al cargar las solicitudes pendientes.')
        return redirect('home')

def lista_retirador(request, retirador_id):
    """
    Vista optimizada para listar solicitudes de un retirador específico.
    Incluye solicitudes asignadas y sin asignar en sus zonas.
    """
    try:
        # Optimizado: prefetch_related para zonas
        retirador = get_object_or_404(
            Retirador.objects.prefetch_related('zonas_preferidas'),
            id=retirador_id
        )
        hoy = timezone.now().date()
        
        # Optimizado: select_related para evitar N+1 queries
        lista = SolicitudRetiro.objects.filter(
            Q(fecha_retiro=hoy) & (
                Q(retirador_asignado=retirador) | 
                Q(retirador_asignado__isnull=True, solicitante__zona__in=retirador.zonas_preferidas.all())
            ) & Q(estado__in=['pendiente', 'asignado'])
        ).select_related(
            'solicitante',
            'solicitante__zona',
            'retirador_asignado'
        ).order_by('hora_solicitud')
        
        context = {
            'retirador': retirador,
            'lista': lista,
            'hoy': hoy,
            'total': lista.count()
        }
        
        return render(request, 'retiros/lista_retirador.html', context)
    
    except Exception as e:
        logger.error(f"Error al listar solicitudes del retirador {retirador_id}: {str(e)}")
        messages.error(request, 'Ocurrió un error al cargar la lista del retirador.')
        return redirect('home')

def home(request):
    """
    Vista optimizada del dashboard principal.
    Muestra estadísticas y resumen de solicitudes por retirador.
    """
    try:
        hoy = timezone.now().date()
        
        # Optimizado: Una sola query para contar pendientes
        total_pendientes = SolicitudRetiro.objects.filter(
            Q(fecha_retiro=hoy) & Q(estado__in=['pendiente', 'asignado'])
        ).count()
        
        # Optimizado: prefetch_related para zonas de retiradores
        retiradores = Retirador.objects.prefetch_related('zonas_preferidas').all()
        
        # Optimizado: Usar annotate para contar en una sola query
        # Preparamos las solicitudes del día con select_related
        solicitudes_hoy = SolicitudRetiro.objects.filter(
            Q(fecha_retiro=hoy) & Q(estado__in=['pendiente', 'asignado'])
        ).select_related('solicitante', 'solicitante__zona', 'retirador_asignado')
        
        resúmenes = []
        for r in retiradores:
            # Filtrar en Python para evitar queries adicionales
            zonas_ids = [z.id for z in r.zonas_preferidas.all()]
            count = sum(
                1 for s in solicitudes_hoy 
                if s.retirador_asignado == r or 
                (s.retirador_asignado is None and s.solicitante.zona_id in zonas_ids)
            )
            resúmenes.append({'retirador': r, 'count': count})
        
        # Total solicitantes registrados
        total_solicitantes = Solicitante.objects.count()
        
        # Solicitantes con datos incompletos
        solicitantes_incompletos = Solicitante.objects.filter(
            Q(email_desconocido=True) | Q(direccion_desconocida=True)
        ).count()
        
        context = {
            'total_pendientes': total_pendientes,
            'resúmenes': resúmenes,
            'total_solicitantes': total_solicitantes,
            'solicitantes_incompletos': solicitantes_incompletos,
            'hoy': hoy,
        }
        
        return render(request, 'retiros/home.html', context)
    
    except Exception as e:
        logger.error(f"Error en dashboard home: {str(e)}")
        messages.error(request, 'Ocurrió un error al cargar el dashboard.')
        # Retornar contexto mínimo para evitar crash
        return render(request, 'retiros/home.html', {
            'total_pendientes': 0,
            'resúmenes': [],
            'total_solicitantes': 0,
            'solicitantes_incompletos': 0,
            'hoy': timezone.now().date(),
        })

def marcar_completado(request, solicitud_id):
    """
    Marca una solicitud como completada.
    Puede ser llamada vía POST o AJAX.
    """
    try:
        solicitud = get_object_or_404(SolicitudRetiro, id=solicitud_id)
        
        if request.method == 'POST':
            solicitud.estado = 'completado'
            solicitud.save()
            
            logger.info(f"Solicitud {solicitud_id} marcada como completada")
            
            # Si es AJAX, retornar JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Solicitud de {solicitud.solicitante.nombre} marcada como completada',
                    'solicitud_id': solicitud_id
                })
            
            # Si no es AJAX, redirigir con mensaje
            messages.success(request, f'Solicitud de {solicitud.solicitante.nombre} marcada como completada.')
            return redirect(request.META.get('HTTP_REFERER', 'lista_pendientes'))
        
        # Si es GET, mostrar confirmación
        return render(request, 'retiros/confirmar_completado.html', {
            'solicitud': solicitud
        })
    
    except Exception as e:
        logger.error(f"Error al marcar solicitud {solicitud_id} como completada: {str(e)}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Error al marcar como completada'
            }, status=500)
        
        messages.error(request, 'Ocurrió un error al marcar la solicitud como completada.')
        return redirect('lista_pendientes')

def exportar_pdf_retirador(request, retirador_id):
    """
    Exporta la lista de retiros de un retirador específico a PDF.
    """
    try:
        retirador = get_object_or_404(
            Retirador.objects.prefetch_related('zonas_preferidas'),
            id=retirador_id
        )
        hoy = timezone.now().date()
        
        # Obtener solicitudes del retirador
        solicitudes = SolicitudRetiro.objects.filter(
            Q(fecha_retiro=hoy) & (
                Q(retirador_asignado=retirador) | 
                Q(retirador_asignado__isnull=True, solicitante__zona__in=retirador.zonas_preferidas.all())
            ) & Q(estado__in=['pendiente', 'asignado'])
        ).select_related(
            'solicitante',
            'solicitante__zona',
            'retirador_asignado'
        ).order_by('hora_solicitud')
        
        # Generar PDF
        return generar_pdf_lista_retiros(solicitudes, retirador, hoy)
    
    except Exception as e:
        logger.error(f"Error al exportar PDF del retirador {retirador_id}: {str(e)}")
        messages.error(request, 'Ocurrió un error al generar el PDF.')
        return redirect('lista_retirador', retirador_id=retirador_id)

def exportar_pdf_general(request):
    """
    Exporta la lista general de retiros pendientes a PDF.
    """
    try:
        hoy = timezone.now().date()
        
        # Obtener todas las solicitudes pendientes del día
        solicitudes = SolicitudRetiro.objects.filter(
            Q(fecha_retiro=hoy) & Q(estado__in=['pendiente', 'asignado'])
        ).select_related(
            'solicitante',
            'solicitante__zona',
            'retirador_asignado'
        ).order_by('retirador_asignado', 'hora_solicitud')
        
        # Generar PDF
        return generar_pdf_lista_retiros(solicitudes, None, hoy)
    
    except Exception as e:
        logger.error(f"Error al exportar PDF general: {str(e)}")
        messages.error(request, 'Ocurrió un error al generar el PDF.')
        return redirect('lista_pendientes')

def notificar_datos_faltantes(request):
    """
    Vista para enviar notificaciones sobre solicitantes con datos faltantes.
    """
    try:
        # Obtener solicitantes con datos incompletos
        solicitantes = Solicitante.objects.filter(
            Q(email_desconocido=True) | Q(direccion_desconocida=True)
        ).select_related('zona')
        
        # Enviar notificaciones
        resultado = enviar_notificacion_datos_faltantes(solicitantes)
        
        if resultado['success']:
            messages.info(request, resultado['message'])
        else:
            messages.error(request, resultado['message'])
        
        return redirect('home')
    
    except Exception as e:
        logger.error(f"Error al notificar datos faltantes: {str(e)}")
        messages.error(request, 'Ocurrió un error al procesar las notificaciones.')
        return redirect('home')
