from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q  # Agregamos esto para Q
from .models import SolicitudRetiro, Retirador, Solicitante
from .forms import SolicitudRetiroForm
from django.utils import timezone
from datetime import timedelta

def agregar_solicitud(request):
    if request.method == 'POST':
        form = SolicitudRetiroForm(request.POST)
        if form.is_valid():
            solicitud = form.save()
            # Lógica simple de asignación por zona (expandimos después)
            if not solicitud.retirador_asignado:
                # Ejemplo: Asigna basado en zona del solicitante
                zona = solicitud.solicitante.zona
                retiradores = Retirador.objects.filter(zonas_preferidas=zona, tipo='fijo')
                if retiradores.exists():
                    solicitud.retirador_asignado = retiradores.first()
                    solicitud.estado = 'asignado'
                    solicitud.save()
            messages.success(request, f'Solicitud agregada para {solicitud.solicitante.nombre}. Asignada a {solicitud.retirador_asignado}.')
            return redirect('lista_pendientes')
    else:
        form = SolicitudRetiroForm()
    return render(request, 'retiros/agregar_solicitud.html', {'form': form})

def lista_pendientes(request):
    hoy = timezone.now().date()
    pendientes = SolicitudRetiro.objects.filter(
        Q(fecha_retiro=hoy) & Q(estado__in=['pendiente', 'asignado'])
    ).order_by('retirador_asignado', 'hora_solicitud')
    return render(request, 'retiros/lista_pendientes.html', {'pendientes': pendientes, 'hoy': hoy})

def lista_retirador(request, retirador_id):
    retirador = get_object_or_404(Retirador, id=retirador_id)
    hoy = timezone.now().date()
    # Corregido: Todo dentro de un Q combinado para evitar el SyntaxError
    lista = SolicitudRetiro.objects.filter(
        Q(fecha_retiro=hoy) & (
            Q(retirador_asignado=retirador) | 
            Q(retirador_asignado__isnull=True, solicitante__zona__in=retirador.zonas_preferidas.all())
        ) & Q(estado__in=['pendiente', 'asignado'])
    ).order_by('hora_solicitud')
    return render(request, 'retiros/lista_retirador.html', {'retirador': retirador, 'lista': lista, 'hoy': hoy})

def home(request):
    hoy = timezone.now().date()
    # Contadores rápidos para el dashboard
    total_pendientes = SolicitudRetiro.objects.filter(
        Q(fecha_retiro=hoy) & Q(estado__in=['pendiente', 'asignado'])
    ).count()
    
    # Lista de retiradores con sus pendientes (para mostrar resúmenes)
    retiradores = Retirador.objects.all()
    resúmenes = []
    for r in retiradores:
        count = SolicitudRetiro.objects.filter(
            Q(fecha_retiro=hoy) & (
                Q(retirador_asignado=r) | 
                Q(retirador_asignado__isnull=True, solicitante__zona__in=r.zonas_preferidas.all())
            ) & Q(estado__in=['pendiente', 'asignado'])
        ).count()
        resúmenes.append({'retirador': r, 'count': count})
    
    # Total solicitantes registrados (para stats)
    total_solicitantes = Solicitante.objects.count()
    
    context = {
        'total_pendientes': total_pendientes,
        'resúmenes': resúmenes,
        'total_solicitantes': total_solicitantes,
        'hoy': hoy,
    }
    return render(request, 'retiros/home.html', context)