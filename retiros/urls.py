from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Nueva: página de inicio
    path('agregar/', views.agregar_solicitud, name='agregar_solicitud'),
    path('pendientes/', views.lista_pendientes, name='lista_pendientes'),
    path('lista/<int:retirador_id>/', views.lista_retirador, name='lista_retirador'),
]