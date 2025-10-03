from django.urls import path
from . import views, api

urlpatterns = [
    # Vistas principales
    path('', views.home, name='home'),
    path('agregar/', views.agregar_solicitud, name='agregar_solicitud'),
    path('pendientes/', views.lista_pendientes, name='lista_pendientes'),
    path('lista/<int:retirador_id>/', views.lista_retirador, name='lista_retirador'),
    
    # Acciones sobre solicitudes
    path('marcar-completado/<int:solicitud_id>/', views.marcar_completado, name='marcar_completado'),
    
    # Exportar PDFs
    path('exportar-pdf/retirador/<int:retirador_id>/', views.exportar_pdf_retirador, name='exportar_pdf_retirador'),
    path('exportar-pdf/general/', views.exportar_pdf_general, name='exportar_pdf_general'),
    
    # Notificaciones
    path('notificar-datos-faltantes/', views.notificar_datos_faltantes, name='notificar_datos_faltantes'),
    
    # API endpoints
    path('api/buscar-solicitantes/', api.buscar_solicitantes, name='api_buscar_solicitantes'),
    path('api/solicitante/<int:solicitante_id>/', api.obtener_solicitante, name='api_obtener_solicitante'),
]
