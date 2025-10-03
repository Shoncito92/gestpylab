"""
Utilidades para GestPyLab
Incluye generación de PDFs, notificaciones, etc.
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.http import HttpResponse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def generar_pdf_lista_retiros(solicitudes, retirador=None, fecha=None):
    """
    Genera un PDF con la lista de retiros para un retirador específico o general.
    
    Args:
        solicitudes: QuerySet de SolicitudRetiro
        retirador: Objeto Retirador (opcional)
        fecha: Fecha de los retiros (opcional)
    
    Returns:
        HttpResponse con el PDF generado
    """
    try:
        # Crear respuesta HTTP
        response = HttpResponse(content_type='application/pdf')
        
        # Nombre del archivo
        if retirador:
            filename = f'lista_retiros_{retirador.nombre.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        else:
            filename = f'lista_retiros_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Crear documento PDF
        doc = SimpleDocTemplate(response, pagesize=A4,
                              rightMargin=30, leftMargin=30,
                              topMargin=30, bottomMargin=30)
        
        # Contenedor para elementos del PDF
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#007bff'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#6c757d'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        # Título
        titulo = "GestPyLab - Sistema de Gestión de Retiros"
        elements.append(Paragraph(titulo, title_style))
        
        # Subtítulo
        if retirador:
            subtitulo = f"Lista de Retiros para: {retirador.nombre}"
        else:
            subtitulo = "Lista General de Retiros"
        
        if fecha:
            subtitulo += f" - Fecha: {fecha.strftime('%d/%m/%Y')}"
        
        elements.append(Paragraph(subtitulo, subtitle_style))
        elements.append(Spacer(1, 20))
        
        # Información adicional
        info_text = f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br/>"
        info_text += f"Total de retiros: {solicitudes.count()}"
        
        info_style = ParagraphStyle(
            'Info',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#495057'),
            spaceAfter=20
        )
        elements.append(Paragraph(info_text, info_style))
        elements.append(Spacer(1, 10))
        
        # Crear tabla de datos
        if solicitudes.exists():
            # Encabezados
            data = [['#', 'Solicitante', 'Tipo', 'Zona', 'Dirección', 'Teléfono', 'Notas']]
            
            # Datos
            for idx, solicitud in enumerate(solicitudes, 1):
                data.append([
                    str(idx),
                    solicitud.solicitante.nombre[:25],
                    solicitud.solicitante.get_tipo_display()[:15],
                    solicitud.solicitante.zona.nombre[:15],
                    solicitud.direccion_retiro[:40] + '...' if len(solicitud.direccion_retiro) > 40 else solicitud.direccion_retiro,
                    solicitud.solicitante.telefono,
                    solicitud.notas[:30] + '...' if len(solicitud.notas) > 30 else solicitud.notas
                ])
            
            # Crear tabla
            table = Table(data, colWidths=[0.5*inch, 1.5*inch, 1*inch, 1*inch, 2*inch, 1*inch, 1.5*inch])
            
            # Estilo de tabla
            table.setStyle(TableStyle([
                # Encabezado
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Contenido
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Primera columna centrada
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                
                # Bordes
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Alternar colores de filas
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            elements.append(table)
        else:
            no_data_text = "No hay retiros programados para mostrar."
            elements.append(Paragraph(no_data_text, styles['Normal']))
        
        # Pie de página
        elements.append(Spacer(1, 30))
        footer_text = "_______________________________________________<br/>"
        footer_text += "Firma del Retirador<br/><br/>"
        footer_text += "<i>Este documento fue generado automáticamente por GestPyLab</i>"
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6c757d'),
            alignment=TA_CENTER
        )
        elements.append(Paragraph(footer_text, footer_style))
        
        # Construir PDF
        doc.build(elements)
        
        logger.info(f"PDF generado exitosamente: {filename}")
        return response
    
    except Exception as e:
        logger.error(f"Error al generar PDF: {str(e)}")
        raise


def enviar_notificacion_datos_faltantes(solicitantes):
    """
    Envía notificaciones sobre solicitantes con datos faltantes.
    Por ahora solo registra en logs, pero puede extenderse para enviar emails.
    
    Args:
        solicitantes: QuerySet de Solicitante con datos incompletos
    
    Returns:
        dict con resultado de la operación
    """
    try:
        count = solicitantes.count()
        
        if count == 0:
            logger.info("No hay solicitantes con datos faltantes")
            return {
                'success': True,
                'message': 'No hay solicitantes con datos faltantes',
                'count': 0
            }
        
        # Log de solicitantes con datos faltantes
        logger.warning(f"Se encontraron {count} solicitantes con datos faltantes:")
        
        for solicitante in solicitantes:
            faltantes = []
            if solicitante.email_desconocido:
                faltantes.append('email')
            if solicitante.direccion_desconocida:
                faltantes.append('dirección')
            
            logger.warning(f"  - {solicitante.nombre}: Faltan {', '.join(faltantes)}")
        
        # TODO: Implementar envío de emails cuando sea necesario
        # from django.core.mail import send_mail
        # send_mail(...)
        
        return {
            'success': True,
            'message': f'Se registraron {count} solicitantes con datos faltantes',
            'count': count
        }
    
    except Exception as e:
        logger.error(f"Error al procesar notificaciones: {str(e)}")
        return {
            'success': False,
            'message': f'Error: {str(e)}',
            'count': 0
        }


def validar_horario_agendamiento():
    """
    Valida si la hora actual está dentro del horario de agendamiento (11:00 - 14:00).
    
    Returns:
        tuple: (bool, str) - (es_valido, mensaje)
    """
    from django.utils import timezone
    
    now = timezone.now()
    hora_actual = now.time()
    
    # Horario permitido: 11:00 - 14:00
    hora_inicio = datetime.strptime('11:00', '%H:%M').time()
    hora_fin = datetime.strptime('14:00', '%H:%M').time()
    
    if hora_inicio <= hora_actual <= hora_fin:
        return True, "Horario válido para agendamiento"
    else:
        return False, f"Fuera de horario. Solo se puede agendar entre 11:00 y 14:00 hrs. Hora actual: {hora_actual.strftime('%H:%M')}"
