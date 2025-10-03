"""
API endpoints para búsqueda y funcionalidades AJAX
"""
from django.http import JsonResponse
from django.db.models import Q
from .models import Solicitante
import logging

logger = logging.getLogger(__name__)

def buscar_solicitantes(request):
    """
    Endpoint para búsqueda dinámica de solicitantes.
    Retorna resultados en formato JSON para autocompletado.
    """
    try:
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return JsonResponse({
                'results': [],
                'message': 'Ingrese al menos 2 caracteres para buscar'
            })
        
        # Búsqueda optimizada con select_related
        solicitantes = Solicitante.objects.filter(
            Q(nombre__icontains=query) |
            Q(email__icontains=query) |
            Q(telefono__icontains=query) |
            Q(direccion_principal__icontains=query)
        ).select_related('zona')[:10]  # Limitar a 10 resultados
        
        results = []
        for s in solicitantes:
            # Determinar si tiene datos completos
            estado = '✓ Completo' if s.tiene_datos_completos else '⚠ Incompleto'
            
            results.append({
                'id': s.id,
                'nombre': s.nombre,
                'tipo': s.get_tipo_display(),
                'zona': s.zona.nombre,
                'telefono': s.telefono,
                'email': s.email if s.email else '(Desconocido)',
                'direccion': s.direccion_principal if s.direccion_principal else '(Desconocida)',
                'horario': s.horario_completo,
                'estado': estado,
                'tiene_datos_completos': s.tiene_datos_completos,
                # Texto para mostrar en el select
                'text': f"{s.nombre} - {s.get_tipo_display()} ({s.zona.nombre})"
            })
        
        return JsonResponse({
            'results': results,
            'count': len(results),
            'query': query
        })
    
    except Exception as e:
        logger.error(f"Error en búsqueda de solicitantes: {str(e)}")
        return JsonResponse({
            'error': 'Error al realizar la búsqueda',
            'message': str(e)
        }, status=500)

def obtener_solicitante(request, solicitante_id):
    """
    Obtiene los detalles completos de un solicitante específico.
    Útil para autocompletar campos del formulario.
    """
    try:
        solicitante = Solicitante.objects.select_related('zona').get(id=solicitante_id)
        
        return JsonResponse({
            'id': solicitante.id,
            'nombre': solicitante.nombre,
            'tipo': solicitante.get_tipo_display(),
            'zona': {
                'id': solicitante.zona.id,
                'nombre': solicitante.zona.nombre
            },
            'telefono': solicitante.telefono,
            'email': solicitante.email,
            'email_desconocido': solicitante.email_desconocido,
            'direccion_principal': solicitante.direccion_principal,
            'direccion_desconocida': solicitante.direccion_desconocida,
            'horario_inicio': solicitante.horario_atencion_inicio.strftime('%H:%M') if solicitante.horario_atencion_inicio else None,
            'horario_fin': solicitante.horario_atencion_fin.strftime('%H:%M') if solicitante.horario_atencion_fin else None,
            'comentarios_horario': solicitante.comentarios_horario_retiro,
            'horario_completo': solicitante.horario_completo,
            'tiene_datos_completos': solicitante.tiene_datos_completos
        })
    
    except Solicitante.DoesNotExist:
        return JsonResponse({
            'error': 'Solicitante no encontrado'
        }, status=404)
    
    except Exception as e:
        logger.error(f"Error al obtener solicitante {solicitante_id}: {str(e)}")
        return JsonResponse({
            'error': 'Error al obtener los datos del solicitante',
            'message': str(e)
        }, status=500)
