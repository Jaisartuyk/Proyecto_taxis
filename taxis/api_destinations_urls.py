"""
URLs para gestión de destinos de carreras
"""
from django.urls import path
from .api_ride_destinations import (
    add_destination,
    update_destination,
    delete_destination,
    list_destinations
)

urlpatterns = [
    # Listar destinos de una carrera
    path('', list_destinations, name='api_list_destinations'),
    
    # Agregar nuevo destino
    path('add/', add_destination, name='api_add_destination'),
    
    # Editar destino específico
    path('<int:destination_id>/', update_destination, name='api_update_destination'),
    
    # Eliminar destino específico
    path('<int:destination_id>/delete/', delete_destination, name='api_delete_destination'),
]
