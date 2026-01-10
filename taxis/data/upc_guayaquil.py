"""
Base de datos local de Unidades de Policía Comunitaria (UPC) en Guayaquil
Actualizado: Enero 2026
"""

UPC_GUAYAQUIL = [
    {
        'id': 'upc_norte_1',
        'nombre': 'UPC Norte - Orellana',
        'direccion': 'Av. Francisco de Orellana y Av. Juan Tanca Marengo',
        'telefono': '+593-4-3709100',
        'lat': -2.1414,
        'lng': -79.8838,
        'zona': 'norte',
        'horario': '24 horas'
    },
    {
        'id': 'upc_sur_1',
        'nombre': 'UPC Sur - 25 de Julio',
        'direccion': 'Av. 25 de Julio y Av. del Bombero',
        'telefono': '+593-4-2444444',
        'lat': -2.2241,
        'lng': -79.9089,
        'zona': 'sur',
        'horario': '24 horas'
    },
    {
        'id': 'upc_centro_1',
        'nombre': 'UPC Centro - Chile',
        'direccion': 'Calle Chile y 10 de Agosto',
        'telefono': '+593-4-2326666',
        'lat': -2.1960,
        'lng': -79.8862,
        'zona': 'centro',
        'horario': '24 horas'
    },
    {
        'id': 'upc_norte_terminal',
        'nombre': 'UPC Terminal Terrestre',
        'direccion': 'Av. Benjamín Carrión - Terminal Terrestre',
        'telefono': '+593-4-2139800',
        'lat': -2.1956,
        'lng': -79.9095,
        'zona': 'norte',
        'horario': '24 horas'
    },
    {
        'id': 'upc_norte_aeropuerto',
        'nombre': 'UPC Aeropuerto José Joaquín de Olmedo',
        'direccion': 'Av. de las Américas - Aeropuerto',
        'telefono': '+593-4-2169000',
        'lat': -2.1606,
        'lng': -79.8897,
        'zona': 'norte',
        'horario': '24 horas'
    },
    {
        'id': 'upc_sur_guasmo',
        'nombre': 'UPC Sur - Guasmo',
        'direccion': 'Coop. Unión de Bananeros - Guasmo Central',
        'telefono': '+593-4-2401234',
        'lat': -2.2456,
        'lng': -79.9234,
        'zona': 'sur',
        'horario': '24 horas'
    },
    {
        'id': 'upc_norte_urdesa',
        'nombre': 'UPC Urdesa',
        'direccion': 'Av. Víctor Emilio Estrada y Ficus',
        'telefono': '+593-4-2881200',
        'lat': -2.1789,
        'lng': -79.9056,
        'zona': 'norte',
        'horario': '24 horas'
    },
    {
        'id': 'upc_samborondon',
        'nombre': 'UPC Samborondón',
        'direccion': 'Av. León Febres Cordero - Samborondón',
        'telefono': '+593-4-2835600',
        'lat': -2.1523,
        'lng': -79.8567,
        'zona': 'samborondon',
        'horario': '24 horas'
    },
    {
        'id': 'upc_centro_malecón',
        'nombre': 'UPC Malecón 2000',
        'direccion': 'Malecón Simón Bolívar',
        'telefono': '+593-4-2565555',
        'lat': -2.1967,
        'lng': -79.8833,
        'zona': 'centro',
        'horario': '24 horas'
    },
    {
        'id': 'upc_norte_kennedy',
        'nombre': 'UPC Kennedy',
        'direccion': 'Av. San Jorge y Av. Luis Orrantia',
        'telefono': '+593-4-2290300',
        'lat': -2.1634,
        'lng': -79.8978,
        'zona': 'norte',
        'horario': '24 horas'
    },
]

# Números de emergencia adicionales
EMERGENCY_CONTACTS = {
    'ecu911': {
        'nombre': 'ECU-911 Sistema Integrado de Seguridad',
        'telefono': '911',
        'whatsapp': '+593-99-911-1911',
        'sms': '+593-99-911-1911',
        'tipo': 'emergencia_general'
    },
    'policia': {
        'nombre': 'Policía Nacional',
        'telefono': '101',
        'tipo': 'policia'
    },
    'bomberos': {
        'nombre': 'Bomberos',
        'telefono': '102',
        'tipo': 'bomberos'
    },
    'cruz_roja': {
        'nombre': 'Cruz Roja',
        'telefono': '131',
        'tipo': 'medico'
    },
}


def get_all_upcs():
    """Retorna todas las UPCs disponibles"""
    return UPC_GUAYAQUIL


def get_upcs_by_zone(zone):
    """Retorna UPCs de una zona específica"""
    return [upc for upc in UPC_GUAYAQUIL if upc['zona'] == zone]


def get_upc_by_id(upc_id):
    """Busca una UPC por su ID"""
    for upc in UPC_GUAYAQUIL:
        if upc['id'] == upc_id:
            return upc
    return None
