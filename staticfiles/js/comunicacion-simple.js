// =====================================================
// VERSIÓN ULTRA-SIMPLIFICADA PARA ARREGLO CRÍTICO DE ERRORES
// =====================================================
console.log('🚀 LOADING comunicacion-simple.js - VERSIÓN SIMPLIFICADA');
console.log('📅 Timestamp de carga:', new Date().toISOString());

// Variables globales mínimas
let map;
let socket;
let Maps_API_KEY;

// Función súper simple para actualizar estado SIN errores
function updateStatus(message, className = 'connected') {
    console.log('🔄 updateStatus llamado:', message);
    try {
        // Buscar elementos de estado de forma segura
        const elements = ['connection-status', 'system-status', 'status'];
        let found = false;
        
        for (const id of elements) {
            const el = document.getElementById(id);
            if (el && el.textContent !== undefined) {
                el.textContent = message;
                found = true;
                console.log('✅ Estado actualizado en:', id);
                break;
            }
        }
        
        if (!found) {
            console.warn('⚠️ Ningún elemento de estado encontrado');
        }
    } catch (error) {
        console.warn('⚠️ Error en updateStatus (ignorado):', error.message);
    }
}

// Inicialización súper simple
async function initSimple() {
    console.log('🚀 Iniciando sistema simplificado...');
    
    try {
        updateStatus('Sistema cargado', 'connected');
        
        // Configurar Google Maps de forma simple
        const response = await fetch('/api/maps-key/');
        const data = await response.json();
        Maps_API_KEY = data.maps_api_key;
        
        if (Maps_API_KEY) {
            console.log('✅ API key obtenida');
            loadGoogleMapsAPI();
        }
        
        // Configurar WebSocket simple
        setupSimpleWebSocket();
        
    } catch (error) {
        console.warn('⚠️ Error en init (continuando):', error.message);
    }
}

function loadGoogleMapsAPI() {
    // Verificar si ya se cargó para evitar duplicados
    if (window.google && window.google.maps) {
        console.log('⚠️ Google Maps ya cargado');
        return;
    }
    
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${Maps_API_KEY}&callback=initMap`;
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
}

function setupSimpleWebSocket() {
    try {
        const wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";
        const wsPath = wsProtocol + window.location.host + '/ws/audio/conductores/';
        
        socket = new WebSocket(wsPath);
        
        socket.onopen = function(e) {
            console.log('✅ WebSocket conectado');
            updateStatus('Conectado', 'connected');
        };
        
        socket.onclose = function(e) {
            console.log('❌ WebSocket desconectado');
            updateStatus('Desconectado', 'disconnected');
        };
        
        socket.onerror = function(error) {
            console.warn('⚠️ Error WebSocket:', error);
        };
        
    } catch (error) {
        console.warn('⚠️ Error configurando WebSocket:', error.message);
    }
}

// Función global para Google Maps
window.initMap = function() {
    console.log('🗺️ Inicializando Google Maps...');
    
    try {
        const mapContainer = document.getElementById("map");
        if (!mapContainer) {
            console.warn('⚠️ Contenedor del mapa no encontrado');
            return;
        }
        
        map = new google.maps.Map(mapContainer, {
            zoom: 14,
            center: { lat: -2.170998, lng: -79.922359 },
            mapTypeId: 'roadmap'
        });
        
        console.log('✅ Mapa inicializado correctamente');
        updateStatus('Mapa cargado', 'connected');
        
    } catch (error) {
        console.warn('⚠️ Error inicializando mapa:', error.message);
    }
};

// Configurar botón de grabación SIN errores
function setupAudioButton() {
    const btn = document.getElementById('record-audio-btn');
    if (!btn) {
        console.warn('⚠️ Botón de grabación no encontrado');
        return;
    }
    
    console.log('✅ Botón de grabación encontrado');
    
    // Solo agregar eventos si el elemento lo soporta
    if (typeof btn.addEventListener === 'function') {
        btn.addEventListener('mousedown', function() {
            console.log('🎤 Inicio grabación');
            updateStatus('Grabando...', 'recording');
            this.style.backgroundColor = '#FF5722';
        });
        
        btn.addEventListener('mouseup', function() {
            console.log('🎤 Fin grabación');
            updateStatus('Listo', 'connected');
            this.style.backgroundColor = '';
        });
        
        console.log('✅ Eventos de audio configurados');
    } else {
        console.warn('⚠️ addEventListener no disponible en botón');
    }
}

// Inicialización cuando DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM LISTO - Iniciando sistema simplificado...');
    initSimple();
    setupAudioButton();
});

console.log('📝 comunicacion-simple.js cargado completamente');