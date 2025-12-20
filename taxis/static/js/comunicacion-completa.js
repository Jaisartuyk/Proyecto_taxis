// =====================================================
// SISTEMA WALKIE-TALKIE COMPLETO - VERSIÓN CORREGIDA
// ✅ CON SOPORTE PARA UBICACIONES EN TIEMPO REAL
// =====================================================
console.log('🚀 LOADING comunicacion-completa.js - VERSIÓN CON CREACIÓN AUTOMÁTICA DE MARCADORES v2.1');
console.log('✅✅✅ VERIFICACIÓN: Si ves este mensaje, el código NUEVO está cargado ✅✅✅');
console.log('📅 Timestamp de carga:', new Date().toISOString());

// Variables globales
let map;
let socket;
let chatSocket;  // WebSocket para chat
let driverMarkers = {};
let audioContext;
let audioQueue = [];
let isPlayingAudio = false;
let mediaRecorderCentral;
let centralAudioStream;
let Maps_API_KEY;

// Almacenamiento persistente del historial de chat por conductor
// Estructura: { driverId: [{ message, sender_name, timestamp, is_sent, ... }] }
let chatHistoryStorage = {};
let currentChatDriverId = null; // ID del conductor con el que estamos chateando actualmente

// Variables de reconexión WebSocket
let wsReconnectAttempts = 0;
let wsMaxReconnectAttempts = 10;
let wsReconnectInterval = 1000;
let wsReconnectTimeout;
let isConnecting = false;  // Bandera para evitar múltiples instancias
let reconnectTimeout = null;  // Timeout de reconexión

// Variables del sistema walkie-talkie
let pendingAudioQueue = [];
let dismissedAudios = new Set();
let currentPlayingAudio = null;

const roomName = "conductores";
const wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";

// Elementos del DOM - se inicializarán después de que el DOM esté listo
let startCentralMicBtn = null;
let stopCentralMicBtn = null;

// Flag para asegurar que solo se inicialice una vez
let systemInitialized = false;
let domReady = false;

// DEBUGGING INICIAL
console.log('🔍 Estado inicial del DOM:', document.readyState);
console.log('🔍 URL actual:', window.location.href);

// Función súper segura para obtener elementos
function safeGetElement(id, retries = 3) {
    console.log(`🔍 Buscando elemento: ${id} (${retries} reintentos)`);
    for (let i = 0; i < retries; i++) {
        try {
            const element = document.getElementById(id);
            if (element) {
                console.log(`✅ Elemento encontrado: ${id} - Tipo:`, element.constructor.name);
                return element;
            } else {
                console.warn(`❌ Elemento ${id} no encontrado en intento ${i + 1}`);
            }
        } catch (error) {
            console.warn(`⚠️ Error buscando elemento ${id}, intento ${i + 1}:`, error);
        }

        if (i < retries - 1) {
            // Esperar un poco antes del siguiente intento
            setTimeout(() => { }, 100);
        }
    }
    return null;
}

// Función para crear elementos faltantes
function ensureRequiredElements() {
    console.log('🔧 Verificando y creando elementos requeridos...');

    const requiredElements = {
        'connection-status': 'div',
        'audio-log': 'div',
        'audio-player': 'audio',
        'record-audio-btn': 'button'
    };

    for (const [id, tagName] of Object.entries(requiredElements)) {
        let element = document.getElementById(id);
        if (!element) {
            console.log(`⚠️ Creando elemento faltante: ${id}`);
            element = document.createElement(tagName);
            element.id = id;

            // Configuraciones específicas según el tipo
            if (id === 'audio-player') {
                element.controls = false;
                element.autoplay = false;
                element.style.display = 'none';
            }

            document.body.appendChild(element);
            console.log(`✅ Elemento ${id} creado`);
        }
    }
}

// Función súper robusta para actualizar estado
function updateStatus(message, className = 'connected') {
    console.log('🔄 updateStatus llamado:', message, className);
    try {
        const elements = ['connection-status', 'system-status', 'status'];
        let found = false;

        for (const id of elements) {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = message;

                // Actualizar clase si el elemento lo soporta
                if (el.className !== undefined) {
                    el.className = className;
                }

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

// Actualizar estado de conexión basado en ambos WebSockets
function updateConnectionStatus() {
    const audioConnected = socket && socket.readyState === WebSocket.OPEN;
    const chatConnected = chatSocket && chatSocket.readyState === WebSocket.OPEN;

    console.log('🔍 Estado WebSockets - Audio:', audioConnected, 'Chat:', chatConnected);

    // Actualizar indicador visual en el header
    const statusIndicator = document.querySelector('.status-indicator span');
    const statusDot = document.querySelector('.status-dot');

    if (audioConnected && chatConnected) {
        if (statusIndicator) statusIndicator.textContent = 'Conectado a Central';
        if (statusDot) {
            statusDot.style.background = '#4CAF50';
            statusDot.style.animation = 'pulse 2s infinite';
        }
        console.log('✅ Sistema completamente conectado');
    } else if (audioConnected || chatConnected) {
        if (statusIndicator) statusIndicator.textContent = 'Conexión Parcial';
        if (statusDot) {
            statusDot.style.background = '#FFC107';
            statusDot.style.animation = 'pulse 1s infinite';
        }
        console.log('⚠️ Conexión parcial');
    } else {
        if (statusIndicator) statusIndicator.textContent = 'Desconectado';
        if (statusDot) {
            statusDot.style.background = '#F44336';
            statusDot.style.animation = 'none';
        }
        console.log('❌ Sistema desconectado');
    }
}

// Configurar Google Maps con carga de conductores
async function loadGoogleMapsAPI() {
    try {
        // Verificar si ya se cargó para evitar duplicados
        if (window.google && window.google.maps) {
            console.log('⚠️ Google Maps ya cargado');
            initMap();
            return;
        }

        // Obtener API key
        const response = await fetch('/api/maps-key/');
        const data = await response.json();
        Maps_API_KEY = data.maps_api_key;

        if (!Maps_API_KEY) {
            console.error('❌ No se pudo obtener la API key de Google Maps');
            return;
        }

        console.log('✅ API key obtenida, cargando Google Maps...');

        const script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?key=${Maps_API_KEY}&callback=initMap`;
        script.async = true;
        script.defer = true;
        script.onerror = function () {
            console.error('❌ Error cargando Google Maps API');
        };
        document.head.appendChild(script);

    } catch (error) {
        console.error('❌ Error configurando Google Maps:', error);
    }
}

// Función global para inicializar Google Maps
window.initMap = function () {
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

        // Cargar ubicaciones de taxis
        loadTaxiLocations();

        // Actualizar ubicaciones cada 30 segundos
        setInterval(loadTaxiLocations, 30000);

    } catch (error) {
        console.warn('⚠️ Error inicializando mapa:', error.message);
    }
};

// Cargar y mostrar ubicaciones de taxis
async function loadTaxiLocations() {
    try {
        console.log('🚖 Cargando ubicaciones de taxis...');
        const response = await fetch('/api/taxis_ubicacion/');

        if (!response.ok) {
            console.warn('⚠️ Error en respuesta del servidor:', response.status);
            return;
        }

        const taxis = await response.json();
        console.log('📍 Taxis recibidos:', taxis.length);

        updateTaxiMarkers(taxis);

    } catch (error) {
        console.warn('⚠️ Error cargando ubicaciones:', error.message);
    }
}

// Actualizar marcadores de taxis en el mapa
function updateTaxiMarkers(taxis) {
    if (!map) {
        console.warn('⚠️ Mapa no inicializado');
        return;
    }

    try {
        // Limpiar marcadores existentes
        Object.values(driverMarkers).forEach(marker => {
            if (marker && typeof marker.setMap === 'function') {
                marker.setMap(null);
            }
        });
        driverMarkers = {};

        // Agregar nuevos marcadores
        taxis.forEach(taxi => {
            if (taxi.latitude && taxi.longitude) {
                const position = {
                    lat: parseFloat(taxi.latitude),
                    lng: parseFloat(taxi.longitude)
                };

                const marker = new google.maps.Marker({
                    position: position,
                    map: map,
                    title: `Conductor: ${taxi.nombre_conductor || 'Sin nombre'}`,
                    icon: {
                        url: '/static/imagenes/logo1.png',
                        scaledSize: new google.maps.Size(24, 24),
                        origin: new google.maps.Point(0, 0),
                        anchor: new google.maps.Point(12, 12)
                    }
                });

                // Ventana de información
                const infoWindow = new google.maps.InfoWindow({
                    content: `
                        <div class="taxi-info-window" style="color: #1a1a1a !important; background: #ffffff !important; padding: 10px; min-width: 200px; font-family: Arial, sans-serif !important;">
                            <h5 style="color: #1a1a1a !important; margin: 0 0 10px 0 !important; font-size: 16px !important; font-weight: bold !important; text-shadow: none !important;">${taxi.nombre_conductor || 'Sin nombre'}</h5>
                            <p style="color: #1a1a1a !important; margin: 5px 0 !important; text-shadow: none !important;"><strong style="color: #000000 !important;">Placa:</strong> ${taxi.placa || 'N/A'}</p>
                            <p style="color: #1a1a1a !important; margin: 5px 0 !important; text-shadow: none !important;"><strong style="color: #000000 !important;">Estado:</strong> ${taxi.disponible ? '✅ Disponible' : '🚗 Ocupado'}</p>
                            <p style="color: #1a1a1a !important; margin: 5px 0 !important; text-shadow: none !important;"><strong style="color: #000000 !important;">Teléfono:</strong> ${taxi.telefono || 'N/A'}</p>
                            <button onclick="openDriverChat(${taxi.id})" style="background: #007bff !important; color: #ffffff !important; border: none !important; padding: 8px 16px !important; border-radius: 4px !important; cursor: pointer !important; margin-top: 10px !important; font-weight: bold !important;">
                                💬 Chat
                            </button>
                        </div>
                    `
                });

                marker.addListener('click', () => {
                    // Cerrar otras ventanas
                    Object.values(driverMarkers).forEach(m => {
                        if (m.infoWindow) {
                            m.infoWindow.close();
                        }
                    });

                    infoWindow.open(map, marker);
                });

                marker.infoWindow = infoWindow;
                driverMarkers[taxi.id] = marker;

                // También guardar por username si existe (para actualizaciones de ubicación)
                if (taxi.username) {
                    driverMarkers[taxi.username] = marker;
                    console.log(`🔑 Marcador guardado con username: ${taxi.username}`);
                }
            }
        });

        console.log(`✅ ${Object.keys(driverMarkers).length} marcadores actualizados`);
        updateStatus(`${Object.keys(driverMarkers).length} conductores en línea`, 'connected');

    } catch (error) {
        console.error('❌ Error actualizando marcadores:', error);
    }
}

// Función para abrir chat con conductor
function openDriverChat(driverId) {
    console.log('💬 Abriendo chat con conductor:', driverId);

    try {
        // Buscar el elemento del conductor en la lista
        const driverElement = document.querySelector(`[data-driver-id="${driverId}"]`);
        let driverName = `Conductor #${driverId}`;

        if (driverElement) {
            const nameElement = driverElement.querySelector('span');
            if (nameElement) {
                driverName = nameElement.textContent;
            }
        }

        // Actualizar el header del chat
        const chatHeader = document.getElementById('chat-header');
        if (chatHeader) {
            chatHeader.innerHTML = `
                <span>💬 Chat con: ${driverName}</span>
                <div class="header-controls">
                    <button class="header-toggle-btn" id="toggle-fullscreen" onclick="toggleFullscreen()" title="Pantalla completa (F11)">🔳</button>
                    <button class="header-toggle-btn minimize" onclick="toggleChat()" title="Ocultar chat (Ctrl+H)">✕</button>
                </div>
            `;
        }

        // Limpiar mensajes anteriores y mostrar el chat
        // NO limpiar el chat log aquí - loadChatHistory lo hará y cargará el historial
        // Solo asegurarse de que el chat log existe
        const chatLog = document.getElementById('chat-log');
        if (!chatLog) {
            console.warn('⚠️ chat-log no encontrado');
        }

        // Mostrar el área de entrada de mensaje
        const inputContainer = document.getElementById('chat-input-container');
        if (inputContainer) {
            inputContainer.style.display = 'flex';
        }

        // Ocultar el mensaje de "no chat seleccionado"
        const noChatSelected = document.getElementById('no-chat-selected');
        if (noChatSelected) {
            noChatSelected.style.display = 'none';
        }

        // Configurar el input para este conductor
        const messageInput = document.getElementById('chat-message-input');
        if (messageInput) {
            messageInput.setAttribute('data-driver-id', driverId);
            messageInput.placeholder = `Escribe un mensaje a ${driverName}...`;
            messageInput.focus();
        }

        // Configurar el botón de envío
        const submitButton = document.getElementById('chat-message-submit');
        if (submitButton) {
            // Remover eventos anteriores
            submitButton.replaceWith(submitButton.cloneNode(true));
            const newSubmitButton = document.getElementById('chat-message-submit');

            newSubmitButton.addEventListener('click', function () {
                sendMessageToDriver(driverId);
            });
        }

        // Configurar Enter en el input
        if (messageInput) {
            messageInput.replaceWith(messageInput.cloneNode(true));
            const newInput = document.getElementById('chat-message-input');

            newInput.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') {
                    sendMessageToDriver(driverId);
                }
            });
        }

        // Hacer visible el chat window si está oculto
        const chatWindow = document.querySelector('.chat-window');
        if (chatWindow) {
            chatWindow.classList.remove('hidden');
        }
        
        // Guardar el ID del conductor actual para guardar mensajes recibidos
        currentChatDriverId = driverId;

        console.log(`✅ Chat iniciado con ${driverName} (ID: ${driverId})`);

        // Cargar historial de chat (ahora con persistencia en localStorage)
        loadChatHistory(driverId);

    } catch (error) {
        console.error('❌ Error abriendo chat:', error);
        alert('Error abriendo el chat. Por favor, intenta de nuevo.');
    }
}

// Función para guardar historial en localStorage
function saveChatHistoryToStorage(driverId, messages) {
    try {
        // Guardar en memoria
        chatHistoryStorage[driverId] = messages;
        
        // Guardar en localStorage para persistencia entre sesiones
        const storageKey = `chat_history_${driverId}`;
        localStorage.setItem(storageKey, JSON.stringify(messages));
        console.log(`💾 Historial guardado para conductor ${driverId}: ${messages.length} mensajes`);
        console.log(`   Último mensaje: ${messages.length > 0 ? messages[messages.length - 1].message.substring(0, 30) : 'N/A'}...`);
    } catch (error) {
        console.error('❌ Error guardando historial en localStorage:', error);
        // Si localStorage está lleno, intentar limpiar historiales antiguos
        if (error.name === 'QuotaExceededError') {
            console.warn('⚠️ localStorage lleno, limpiando historiales antiguos...');
            // Limpiar historiales de conductores que no están activos
            // Por ahora, solo loguear el error
        }
    }
}

// Función para cargar historial desde localStorage
function loadChatHistoryFromStorage(driverId) {
    try {
        // Primero intentar desde memoria
        if (chatHistoryStorage[driverId]) {
            console.log(`📂 Historial cargado desde memoria para conductor ${driverId}`);
            return chatHistoryStorage[driverId];
        }
        
        // Si no está en memoria, intentar desde localStorage
        const storageKey = `chat_history_${driverId}`;
        const stored = localStorage.getItem(storageKey);
        if (stored) {
            const messages = JSON.parse(stored);
            chatHistoryStorage[driverId] = messages; // Guardar en memoria también
            console.log(`📂 Historial cargado desde localStorage para conductor ${driverId}: ${messages.length} mensajes`);
            return messages;
        }
        
        return [];
    } catch (error) {
        console.error('❌ Error cargando historial desde localStorage:', error);
        return [];
    }
}

// Función para agregar un mensaje al historial guardado
function addMessageToHistory(driverId, message) {
    if (!chatHistoryStorage[driverId]) {
        chatHistoryStorage[driverId] = [];
    }
    
    // Agregar mensaje al historial
    chatHistoryStorage[driverId].push(message);
    
    // Guardar en localStorage
    saveChatHistoryToStorage(driverId, chatHistoryStorage[driverId]);
}

// Función para renderizar mensajes en el chat log
function renderMessages(messages) {
    console.log(`\n📝 ========================================`);
    console.log(`📝 renderMessages() llamada con ${messages ? messages.length : 0} mensajes`);
    console.log(`📝 Tipo de messages:`, typeof messages, Array.isArray(messages));
    
    const chatLog = document.getElementById('chat-log');
    if (!chatLog) {
        console.error('❌ chat-log no encontrado para renderizar mensajes');
        return;
    }
    console.log(`📝 chat-log encontrado:`, chatLog);
    
    // IMPORTANTE: Ocultar el mensaje "no-chat-selected" si existe
    const noChatSelected = document.getElementById('no-chat-selected');
    if (noChatSelected) {
        noChatSelected.style.display = 'none';
        console.log(`📝 Ocultado #no-chat-selected`);
    }
    
    // Limpiar chat log completamente
    chatLog.innerHTML = '';
    
    // Asegurar que el chat log sea visible
    chatLog.style.display = 'block';
    chatLog.style.visibility = 'visible';
    chatLog.style.opacity = '1';
    
    // Si no hay mensajes, mostrar mensaje de "sin mensajes"
    if (!messages || messages.length === 0) {
        console.log(`📝 No hay mensajes, mostrando mensaje vacío`);
        chatLog.innerHTML = `
            <div style="text-align: center; padding: 20px; color: #7f8c8d;">
                <strong>💬 No hay mensajes aún</strong><br>
                <small>Los mensajes aparecerán aquí...</small>
            </div>
        `;
        return;
    }
    
    // Agregar mensajes al chat
    console.log(`📝 Renderizando ${messages.length} mensajes en el chat log...`);
    messages.forEach((msg, index) => {
        console.log(`📝 Mensaje ${index + 1}:`, {
            sender_id: msg.sender_id,
            sender_name: msg.sender_name,
            message: msg.message ? msg.message.substring(0, 30) + '...' : 'SIN MENSAJE',
            is_sent: msg.is_sent,
            timestamp: msg.timestamp
        });
        // El backend devuelve: {sender_id, sender_name, message, timestamp, is_sent}
        const isSent = msg.is_sent === true || msg.sender_id == 1;
        const timestamp = typeof msg.timestamp === 'string'
            ? (msg.timestamp.includes('T') ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : msg.timestamp)
            : new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        // Usar el mismo formato que en comunicacion_driver.html para consistencia
        // IMPORTANTE: Asegurar que los mensajes sean visibles con estilos inline
        const messageHtml = `
            <div class="message ${isSent ? 'sent' : 'received'}" 
                 style="display: block !important; 
                        visibility: visible !important; 
                        opacity: 1 !important;
                        margin-bottom: 10px; 
                        padding: 8px 12px; 
                        background: ${isSent ? '#007bff' : '#e9ecef'}; 
                        color: ${isSent ? 'white' : 'black'}; 
                        border-radius: 8px; 
                        max-width: 70%; 
                        ${isSent ? 'margin-left: auto;' : 'margin-right: auto;'}
                        position: relative;
                        z-index: 2;
                        width: auto;
                        min-width: 100px;">
                <div style="font-weight: bold; margin-bottom: 4px; display: block;">${isSent ? 'Central' : (msg.sender_name || 'Desconocido')}</div>
                <div style="display: block; word-wrap: break-word;">${msg.message}</div>
                <div class="message-time" style="font-size: 0.8em; opacity: 0.8; margin-top: 4px; display: block;">${timestamp}</div>
            </div>
        `;
        chatLog.insertAdjacentHTML('beforeend', messageHtml);
        
        // Log cada 10 mensajes para no saturar la consola
        if ((index + 1) % 10 === 0 || index === messages.length - 1) {
            console.log(`   ✅ ${index + 1}/${messages.length} mensajes agregados al DOM`);
        }
    });
    
    // Verificar que los mensajes se agregaron correctamente
    const renderedMessages = chatLog.querySelectorAll('.message');
    console.log(`✅ Todos los mensajes renderizados. Total en DOM: ${renderedMessages.length}`);
    if (renderedMessages.length === 0 && messages.length > 0) {
        console.error(`❌ ERROR: Se intentaron renderizar ${messages.length} mensajes pero 0 aparecieron en el DOM!`);
        console.error(`   chatLog.innerHTML length:`, chatLog.innerHTML.length);
        console.error(`   chatLog.children:`, chatLog.children.length);
    }
    console.log(`📝 ========================================\n`);
    
    // Scroll al final
    chatLog.scrollTop = chatLog.scrollHeight;
}

// Cargar historial de chat con un conductor (CON PERSISTENCIA)
async function loadChatHistory(driverId) {
    try {
        console.log(`📜 ========================================`);
        console.log(`📜 loadChatHistory() llamada para conductor ${driverId}...`);
        console.log(`📜 ========================================`);
        
        const chatLog = document.getElementById('chat-log');
        if (!chatLog) {
            console.error('❌ chat-log no encontrado en loadChatHistory');
            return;
        }
        console.log(`✅ chat-log encontrado:`, chatLog);
        
        // Verificar si ya hay mensajes renderizados (no limpiar si ya hay contenido)
        const existingMessages = chatLog.querySelectorAll('.message');
        const hasExistingMessages = existingMessages.length > 0;
        console.log(`📊 Mensajes existentes en DOM: ${existingMessages.length}`);
        
        // Solo limpiar si no hay mensajes o si hay un placeholder
        if (!hasExistingMessages || chatLog.innerHTML.includes('Cargando historial') || chatLog.innerHTML.includes('No hay mensajes')) {
            chatLog.innerHTML = '';
            console.log(`🧹 chat-log limpiado (no había mensajes reales)`);
        } else {
            console.log(`✅ Manteniendo ${existingMessages.length} mensajes existentes`);
        }
        
        // Ocultar el mensaje de "no chat seleccionado" si existe
        const noChatSelected = document.getElementById('no-chat-selected');
        if (noChatSelected) {
            noChatSelected.style.display = 'none';
            noChatSelected.style.visibility = 'hidden';
            noChatSelected.style.opacity = '0';
            console.log(`🚫 #no-chat-selected ocultado`);
        }
        
        // Primero intentar cargar desde el atributo data-initial-history del elemento del conductor
        const driverElement = document.querySelector(`[data-driver-id="${driverId}"]`);
        let initialHistory = [];
        if (driverElement && driverElement.hasAttribute('data-initial-history')) {
            try {
                const historyJson = driverElement.getAttribute('data-initial-history');
                initialHistory = JSON.parse(historyJson);
                console.log(`📦 Historial inicial desde data-initial-history: ${initialHistory.length} mensajes`);
                // Guardar en localStorage para consistencia
                if (initialHistory.length > 0) {
                    saveChatHistoryToStorage(driverId, initialHistory);
                    console.log(`💾 Historial inicial guardado en localStorage`);
                    // Renderizar inmediatamente
                    renderMessages(initialHistory);
                    console.log(`✅ Historial inicial renderizado`);
                }
            } catch (parseError) {
                console.error('❌ Error parseando data-initial-history:', parseError);
            }
        }
        
        // Luego cargar desde almacenamiento local (historial guardado) - MUY RÁPIDO
        const storedMessages = loadChatHistoryFromStorage(driverId);
        console.log(`📂 Mensajes en localStorage: ${storedMessages.length}`);
        
        // Si hay mensajes guardados y no se cargó desde initialHistory, mostrarlos inmediatamente
        if (storedMessages.length > 0 && initialHistory.length === 0) {
            console.log(`📂 Mostrando ${storedMessages.length} mensajes guardados localmente`);
            renderMessages(storedMessages);
        } else if (storedMessages.length === 0 && initialHistory.length === 0) {
            // Si no hay mensajes guardados ni iniciales, mostrar indicador de carga
            chatLog.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #7f8c8d; display: block !important; visibility: visible !important;">
                    <strong>💬 Cargando historial...</strong><br>
                    <small>Espera un momento...</small>
                </div>
            `;
            console.log(`⏳ Mostrando indicador de carga`);
        }

        // Luego cargar desde el servidor para obtener mensajes nuevos/actualizados
        try {
            const response = await fetch(`/api/chat_history/${driverId}/`);
            if (!response.ok) {
                console.warn('⚠️ No se pudo cargar el historial del servidor');
                // Si no se puede cargar del servidor pero tenemos mensajes guardados, mantener esos
                if (storedMessages.length > 0) {
                    console.log('📂 Manteniendo mensajes guardados localmente');
                    return;
                }
                // Si no hay mensajes guardados y falla el servidor, mostrar error
                chatLog.innerHTML = `
                    <div style="text-align: center; padding: 20px; color: #e74c3c;">
                        <strong>⚠️ Error cargando historial</strong><br>
                        <small>No se pudo conectar al servidor</small>
                    </div>
                `;
                return;
            }

            const payload = await response.json();
            console.log(`📦 Payload completo del servidor:`, payload);
            
            // El servidor puede devolver {messages: [...]} o directamente un array
            let serverMessages = [];
            if (Array.isArray(payload)) {
                serverMessages = payload;
            } else if (payload.messages && Array.isArray(payload.messages)) {
                serverMessages = payload.messages;
            } else {
                console.warn('⚠️ Formato de respuesta inesperado:', payload);
                serverMessages = [];
            }
            
            console.log(`✅ Historial del servidor: ${serverMessages.length || 0} mensajes`);
            if (serverMessages.length > 0) {
                console.log(`   Primer mensaje:`, serverMessages[0]);
                console.log(`   Último mensaje:`, serverMessages[serverMessages.length - 1]);
            }
            
            // Si hay mensajes del servidor, actualizar el almacenamiento
            if (serverMessages.length > 0) {
                // IMPORTANTE: Guardar historial completo del servidor (es la fuente de verdad)
                saveChatHistoryToStorage(driverId, serverMessages);
                
                // Verificar si ya hay mensajes renderizados (usar la variable guardada)
                const hasExisting = window._hasExistingMessages || false;
                const currentMessages = chatLog.querySelectorAll('.message');
                
                if (hasExisting && currentMessages.length > 0) {
                    // Si ya hay mensajes, solo actualizar si el servidor tiene más mensajes
                    console.log(`✅ Ya hay ${currentMessages.length} mensajes renderizados. El servidor tiene ${serverMessages.length} mensajes.`);
                    if (serverMessages.length > currentMessages.length) {
                        console.log(`📝 Actualizando con ${serverMessages.length} mensajes del servidor (más que los existentes)`);
                        renderMessages(serverMessages);
                    } else {
                        console.log(`✅ Manteniendo mensajes existentes (servidor no tiene más mensajes)`);
                    }
                } else {
                    // Si no hay mensajes renderizados, renderizar los del servidor
                    console.log(`✅ Renderizando ${serverMessages.length} mensajes del servidor`);
                    renderMessages(serverMessages);
                }
                
                // Verificar que los mensajes se renderizaron
                setTimeout(() => {
                    const renderedMessages = chatLog.querySelectorAll('.message');
                    console.log(`   ✅ Mensajes finales en DOM: ${renderedMessages.length}`);
                    if (renderedMessages.length === 0 && serverMessages.length > 0) {
                        console.error('❌ ERROR: Los mensajes no se renderizaron correctamente!');
                    }
                }, 100);
            } else if (storedMessages.length > 0) {
                // Si el servidor no tiene mensajes pero tenemos guardados, mostrar los guardados solo si no hay mensajes renderizados
                const currentMessages = chatLog.querySelectorAll('.message');
                if (currentMessages.length === 0) {
                    console.log('📂 Mostrando mensajes guardados localmente (servidor vacío, no hay mensajes renderizados)');
                    renderMessages(storedMessages);
                } else {
                    console.log('✅ Manteniendo mensajes renderizados (servidor vacío pero hay mensajes en DOM)');
                }
            } else {
                // No hay mensajes ni en servidor ni guardados
                const currentMessages = chatLog.querySelectorAll('.message');
                if (currentMessages.length === 0) {
                    console.log('📭 No hay mensajes en servidor ni guardados localmente ni renderizados');
                    renderMessages([]);
                } else {
                    console.log('✅ Manteniendo mensajes renderizados');
                }
            }

        } catch (fetchError) {
            console.error('❌ Error en fetch del historial:', fetchError);
            // En caso de error, intentar mostrar mensajes guardados
            if (storedMessages.length > 0) {
                console.log('📂 Mostrando mensajes guardados como respaldo');
                renderMessages(storedMessages);
            } else {
                chatLog.innerHTML = `
                    <div style="text-align: center; padding: 20px; color: #e74c3c;">
                        <strong>⚠️ Error cargando historial</strong><br>
                        <small>${fetchError.message}</small>
                    </div>
                `;
            }
        }

    } catch (error) {
        console.error('❌ Error cargando historial:', error);
        const chatLog = document.getElementById('chat-log');
        if (chatLog) {
            chatLog.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #e74c3c;">
                    <strong>❌ Error cargando historial</strong><br>
                    <small>${error.message}</small>
                </div>
            `;
        }
    }
}

// Función para enviar mensaje a conductor específico
function sendMessageToDriver(driverId) {
    const input = document.getElementById('chat-message-input');
    if (!input || !input.value.trim()) {
        return;
    }

    const message = input.value.trim();
    console.log('📤 Enviando mensaje a conductor:', driverId, message);

    try {
        // Crear objeto de mensaje para guardar en historial
        const messageObj = {
            message: message,
            sender_name: 'Central',
            sender_id: 1,
            is_sent: true,
            timestamp: new Date().toISOString()
        };
        
        // Guardar mensaje en historial
        addMessageToHistory(driverId, messageObj);
        
        // Agregar mensaje al chat log inmediatamente (usar la misma estructura que renderMessages)
        const chatLog = document.getElementById('chat-log');
        if (chatLog) {
            // Ocultar placeholder si existe
            const noChatSelected = document.getElementById('no-chat-selected');
            if (noChatSelected) {
                noChatSelected.style.display = 'none';
                noChatSelected.style.visibility = 'hidden';
                noChatSelected.style.opacity = '0';
            }
            
            // Limpiar placeholder de "No hay mensajes"
            const placeholder = chatLog.querySelector('div[style*="text-align: center"]');
            if (placeholder && placeholder.innerHTML.includes('No hay mensajes')) {
                placeholder.remove();
            }
            
            const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message sent';
            messageDiv.style.cssText = 'display: block !important; visibility: visible !important; opacity: 1 !important; margin-bottom: 10px; padding: 8px 12px; background: #007bff; color: white; border-radius: 8px; max-width: 70%; margin-left: auto; position: relative; z-index: 2;';
            
            messageDiv.innerHTML = `
                <div style="font-weight: bold; margin-bottom: 4px; display: block;">Central</div>
                <div style="display: block; word-wrap: break-word;">${message}</div>
                <div class="message-time" style="font-size: 0.8em; opacity: 0.8; margin-top: 4px; display: block;">${timestamp}</div>
            `;
            
            chatLog.appendChild(messageDiv);
            chatLog.scrollTop = chatLog.scrollHeight;
            console.log(`✅ Mensaje agregado al chat log: ${message}`);
        }

        // Enviar por WebSocket de Chat
        if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
            chatSocket.send(JSON.stringify({
                'message': message,
                'recipient_id': driverId,
                'sender_id': 'admin'
            }));

            console.log('✅ Mensaje enviado por Chat WebSocket');
        } else {
            console.warn('⚠️ Chat WebSocket no disponible - mensaje no enviado');

            // Mostrar error en el chat
            if (chatLog) {
                const errorHtml = `
                    <div style="text-align: center; color: #e74c3c; padding: 10px; font-style: italic;">
                        ⚠️ Error: Sin conexión. Mensaje no enviado.
                    </div>
                `;
                chatLog.insertAdjacentHTML('beforeend', errorHtml);
            }
        }

        // Limpiar input
        input.value = '';

    } catch (error) {
        console.error('❌ Error enviando mensaje:', error);

        // Mostrar error en el chat
        const chatLog = document.getElementById('chat-log');
        if (chatLog) {
            const errorHtml = `
                <div style="text-align: center; color: #e74c3c; padding: 10px; font-style: italic;">
                    ❌ Error enviando mensaje: ${error.message}
                </div>
            `;
            chatLog.insertAdjacentHTML('beforeend', errorHtml);
        }
    }
}

// Función legacy para compatibilidad (mantener pero redirigir)
function sendChatMessage(driverId) {
    console.log('🔄 Redirigiendo sendChatMessage a sendMessageToDriver');
    sendMessageToDriver(driverId);
}

// Configurar WebSocket - CÓDIGO FUNCIONAL DEL CONDUCTOR
function setupWebSocket() {
    // Evitar múltiples llamadas simultáneas
    if (isConnecting) {
        console.log('⚠️ Ya hay una conexión en progreso, ignorando...');
        return;
    }

    // Limpiar timeout de reconexión anterior
    if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
        reconnectTimeout = null;
    }

    // Cerrar conexiones anteriores si existen
    if (socket && socket.readyState !== WebSocket.CLOSED) {
        console.log('🔌 Cerrando Audio WebSocket anterior...');
        socket.close();
    }
    if (chatSocket && chatSocket.readyState !== WebSocket.CLOSED) {
        console.log('🔌 Cerrando Chat WebSocket anterior...');
        chatSocket.close();
    }

    isConnecting = true;
    console.log('🔌 Iniciando WebSockets (Audio + Chat)...');

    const wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";
    const host = window.location.host;

    // 1. Audio WebSocket
    console.log('🔊 Conectando Audio WebSocket...');
    const audioWsUrl = `${wsProtocol}${host}/ws/audio/conductores/`;
    console.log('🔊 URL del Audio WS:', audioWsUrl);
    socket = new WebSocket(audioWsUrl);

    socket.onopen = () => {
        console.log('✅ Audio WS Conectado exitosamente');
        isConnecting = false;
        updateConnectionStatus();
        wsReconnectAttempts = 0;
    };

    socket.onclose = () => {
        console.log('🔊 Audio WS Desconectado');
        isConnecting = false;
        updateConnectionStatus();

        // Reconectar solo si no hay otro timeout pendiente
        if (wsReconnectAttempts < wsMaxReconnectAttempts && !reconnectTimeout) {
            wsReconnectAttempts++;
            console.log(`🔄 Reintentando conexión (${wsReconnectAttempts}/${wsMaxReconnectAttempts})...`);
            reconnectTimeout = setTimeout(() => {
                reconnectTimeout = null;
                setupWebSocket();
            }, wsReconnectInterval * wsReconnectAttempts);
        }
    };

    socket.onerror = (error) => {
        console.error('🔊 Audio WS Error:', error);
        isConnecting = false;
    };

    socket.onmessage = (e) => {
        console.log('🔊 Audio WebSocket recibió mensaje RAW:', e.data.substring(0, 200));
        try {
            const data = JSON.parse(e.data);
            console.log('🔊 Audio WebSocket mensaje parseado:', {
                type: data.type,
                hasAudioData: !!data.audio_data,
                hasAudio: !!data.audio,
                senderId: data.senderId || data.sender_id,
                senderRole: data.senderRole || data.sender_role
            });
            handleWebSocketMessage(data);
        } catch (error) {
            console.error('⚠️ Error procesando mensaje de audio:', error);
        }
    };

    // 2. Chat WebSocket
    console.log('💬 Conectando Chat WebSocket...');
    const chatWsUrl = `${wsProtocol}${host}/ws/chat/`;
    console.log('💬 URL del Chat WS:', chatWsUrl);
    chatSocket = new WebSocket(chatWsUrl);

    chatSocket.onopen = () => {
        console.log('✅ Chat WS Conectado exitosamente');
        updateConnectionStatus();
    };

    chatSocket.onclose = () => {
        console.log('💬 Chat WS Desconectado');
        updateConnectionStatus();

        // Reconectar solo si no hay otro timeout pendiente
        if (!reconnectTimeout) {
            reconnectTimeout = setTimeout(() => {
                reconnectTimeout = null;
                setupWebSocket();
            }, 5000);
        }
    };

    chatSocket.onerror = (error) => {
        console.error('💬 Chat WS Error:', error);
    };

    chatSocket.onmessage = (e) => {
        console.log('💬 Mensaje recibido:', e.data);
        try {
            const data = JSON.parse(e.data);
            handleChatMessage(data);
        } catch (error) {
            console.warn('⚠️ Error procesando mensaje de chat:', error);
        }
    };
}

// Manejar mensajes WebSocket
function handleWebSocketMessage(data) {
    console.log('📨 Procesando mensaje:', data.type);

    switch (data.type) {
        case 'audio_message':
        case 'central_audio':  // Audio de la central a conductores
        case 'audio_broadcast':  // Audio broadcast desde el servidor
            handleAudioMessage(data);
            break;
        case 'chat_message':
            handleChatMessage(data);
            break;
        case 'driver_status':
            handleDriverStatusUpdate(data);
            break;
        case 'location':
        case 'location_update':
        case 'driver_location_update':  // ✅ Agregar soporte para ubicaciones desde app móvil
            handleLocationUpdate(data);
            break;
        default:
            console.log('ℹ️ Tipo de mensaje no manejado:', data.type);
    }
}

// Manejar mensaje de audio
function handleAudioMessage(data) {
    console.log('🎵 Mensaje de audio recibido', data);

    try {
        // Obtener audio_data de diferentes formatos posibles
        const audioData = data.audio_data || data.audio;

        if (audioData) {
            // Determinar el origen del audio
            let sender = 'Desconocido';
            let senderId = 'unknown';

            if (data.type === 'central_audio') {
                // Audio de la central (no debería llegar aquí, pero por si acaso)
                sender = 'Central';
                senderId = 'central';
            } else if (data.senderId || data.sender_id || data.driver_id) {
                // Audio de un conductor
                senderId = data.senderId || data.sender_id || data.driver_id;
                sender = data.senderName || data.sender_name || `Conductor #${senderId}`;
            }

            console.log(`🎵 Reproduciendo audio de: ${sender} (${audioData.length} bytes)`);

            // Reproducir audio inmediatamente usando el mismo método del conductor
            const audioBlob = base64ToBlob(audioData, 'audio/webm');
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);

            audio.play()
                .then(() => {
                    console.log('✅ Audio reproducido correctamente');
                    updateAudioLog(`🔊 Audio de ${sender}`);
                })
                .catch(err => {
                    console.error('❌ Error reproduciendo audio:', err);
                    updateAudioLog(`❌ Error reproduciendo audio de ${sender}`);
                });

        } else {
            console.warn('⚠️ Mensaje de audio sin datos. Keys disponibles:', Object.keys(data));
        }
    } catch (error) {
        console.error('❌ Error procesando audio:', error);
    }
}

// Función helper para convertir base64 a Blob
function base64ToBlob(base64, mimeType) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
}

// Manejar actualización de ubicación en tiempo real
function handleLocationUpdate(data) {
    console.log('📍 Actualización de ubicación recibida:', data);
    console.log('🔍 DEBUG: handleLocationUpdate - Versión con creación automática de marcadores');

    const driverId = data.driverId || data.driver_id;
    const latitude = data.latitude;
    const longitude = data.longitude;
    const source = data.source || 'web';  // 'mobile' o 'web'
    const timestamp = data.timestamp || '';

    if (!driverId || !latitude || !longitude) {
        console.warn('⚠️ Datos de ubicación incompletos:', data);
        return;
    }

    const sourceIcon = source === 'mobile' ? '📱' : '🌐';
    console.log(`${sourceIcon} Ubicación actualizada: ${driverId} (${source}) - ${latitude}, ${longitude}`);
    if (timestamp) {
        console.log(`⏰ Timestamp: ${timestamp}`);
    }

    if (!map) {
        console.warn('⚠️ Mapa no inicializado aún');
        return;
    }

    // Buscar marcador existente (por ID numérico o por username)
    let marker = null;
    let markerKey = null;

    // Primero intentar por ID directo
    if (window.driverMarkers && window.driverMarkers[driverId]) {
        marker = window.driverMarkers[driverId];
        markerKey = driverId;
    } else {
        // Si no existe, buscar por username en los marcadores existentes
        // (Flutter puede enviar username en vez de ID)
        for (const [key, existingMarker] of Object.entries(window.driverMarkers || {})) {
            // Verificar si el marcador tiene info que coincida con el driverId
            if (existingMarker && existingMarker.title && existingMarker.title.toLowerCase().includes(driverId.toLowerCase())) {
                marker = existingMarker;
                markerKey = key;
                console.log(`🔍 Marcador encontrado por username: ${key}`);
                break;
            }
        }
    }

    const newPosition = { lat: parseFloat(latitude), lng: parseFloat(longitude) };

    console.log(`🔍 DEBUG: marker encontrado?`, marker ? 'SÍ' : 'NO');
    console.log(`🔍 DEBUG: window.driverMarkers existe?`, !!window.driverMarkers);
    console.log(`🔍 DEBUG: driverId buscado:`, driverId);

    if (marker) {
        // Actualizar marcador existente
        marker.setPosition(newPosition);
        console.log(`✅ Marcador de ${driverId} actualizado en el mapa (origen: ${source})`);
    } else {
        // Crear nuevo marcador si no existe
        console.log(`🆕 Creando nuevo marcador para ${driverId} (origen: ${source})`);
        console.log(`🔍 DEBUG: Entrando a bloque de creación de marcador`);
        const newMarker = new google.maps.Marker({
            position: newPosition,
            map: map,
            title: `Conductor: ${driverId}`,
            icon: {
                url: '/static/imagenes/logo1.png',
                scaledSize: new google.maps.Size(24, 24),
                origin: new google.maps.Point(0, 0),
                anchor: new google.maps.Point(12, 12)
            }
        });

        // Guardar el marcador (usar driverId como key)
        if (!window.driverMarkers) {
            window.driverMarkers = {};
        }
        window.driverMarkers[driverId] = newMarker;

        // InfoWindow básico
        const infoWindow = new google.maps.InfoWindow({
            content: `
                <div class="taxi-info-window" style="color: #1a1a1a !important; background: #ffffff !important; padding: 10px; min-width: 180px; font-family: Arial, sans-serif !important;">
                    <h5 style="color: #1a1a1a !important; margin: 0 0 10px 0 !important; font-size: 16px !important; font-weight: bold !important; text-shadow: none !important;">${driverId}</h5>
                    <p style="color: #1a1a1a !important; margin: 5px 0 !important; text-shadow: none !important;"><strong style="color: #000000 !important;">Origen:</strong> ${source === 'mobile' ? '📱 App Móvil' : '🌐 Web'}</p>
                    <p style="color: #1a1a1a !important; margin: 5px 0 !important; text-shadow: none !important;"><strong style="color: #000000 !important;">Ubicación:</strong> ${latitude.toFixed(4)}, ${longitude.toFixed(4)}</p>
                </div>
            `
        });

        newMarker.addListener('click', () => {
            infoWindow.open(map, newMarker);
        });

        console.log(`✅ Marcador creado y agregado al mapa para ${driverId}`);
    }
}

// Manejar mensaje de chat
function handleChatMessage(data) {
    console.log('💬 Mensaje de chat recibido:', data);

    try {
        const chatLog = document.getElementById('chat-log');
        if (!chatLog) {
            console.warn('⚠️ chat-log no encontrado');
            return;
        }

        // Extraer datos del mensaje (compatible con ambos formatos)
        const message = data.message;
        const senderId = data.sender_id || data.driver_id;
        const senderName = data.sender_name || `Conductor #${senderId}`;

        if (!message || !senderId) {
            console.warn('⚠️ Mensaje incompleto:', data);
            return;
        }

        // Solo mostrar mensajes de otros usuarios (no los míos)
        if (senderId == currentUser.id) {
            console.log('⏭️ Ignorando mensaje propio');
            return;
        }

        console.log(`✅ Mostrando mensaje de ${senderName}: ${message}`);
        
        // Crear objeto de mensaje para guardar en historial
        const messageObj = {
            message: message,
            sender_name: senderName,
            sender_id: parseInt(senderId),
            is_sent: false,
            timestamp: new Date().toISOString()
        };
        
        // Guardar mensaje en historial (siempre, sin importar si hay chat activo)
        // Esto asegura que los mensajes se guarden incluso si el chat no está abierto
        addMessageToHistory(senderId, messageObj);
        
        // Si el chat está abierto para este conductor, también agregarlo visualmente
        if (currentChatDriverId && currentChatDriverId == senderId) {
            // El mensaje ya se está mostrando visualmente abajo, solo lo guardamos
        }

        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const messageHtml = `
            <div class="message incoming" style="margin-bottom: 10px; padding: 8px 12px; background: #e9ecef; color: black; border-radius: 8px; max-width: 70%; margin-right: auto;">
                <strong>${senderName}:</strong> ${message}
                <div style="font-size: 0.8em; opacity: 0.8;">${timestamp}</div>
            </div>
        `;
        chatLog.insertAdjacentHTML('beforeend', messageHtml);
        chatLog.scrollTop = chatLog.scrollHeight;

        // Remover placeholder si existe
        const placeholder = chatLog.querySelector('div[style*="text-align: center"]');
        if (placeholder) placeholder.remove();

    } catch (error) {
        console.error('❌ Error procesando mensaje de chat:', error);
    }
}

// Configurar sistema de audio
function setupAudioSystem() {
    console.log('🎵 Configurando sistema de audio...');

    try {
        // Configurar AudioContext
        if (window.AudioContext || window.webkitAudioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('✅ AudioContext creado');
        } else {
            console.warn('⚠️ AudioContext no soportado');
        }

        // Configurar botón de grabación
        setupRecordingButton();

    } catch (error) {
        console.error('❌ Error configurando audio:', error);
    }
}

// Configurar botón de grabación
function setupRecordingButton() {
    const btn = safeGetElement('record-audio-btn');
    if (!btn) {
        console.warn('⚠️ Botón de grabación no encontrado');
        return;
    }

    console.log('✅ Configurando botón de grabación...');

    // Verificar que el elemento soporte eventos
    if (typeof btn.addEventListener === 'function') {
        btn.addEventListener('mousedown', startRecording);
        btn.addEventListener('mouseup', stopRecording);
        btn.addEventListener('mouseleave', stopRecording);
        btn.addEventListener('touchstart', startRecording);
        btn.addEventListener('touchend', stopRecording);

        console.log('✅ Eventos de grabación configurados');
    } else {
        console.warn('⚠️ addEventListener no disponible en botón');
    }
}

// Iniciar grabación
async function startRecording() {
    console.log('🎤 Iniciando grabación...');

    try {
        updateStatus('Grabando...', 'recording');

        // Cambiar estilo del botón
        const btn = safeGetElement('record-audio-btn');
        if (btn && btn.style) {
            btn.style.backgroundColor = '#FF5722';
        }

        // Obtener acceso al micrófono
        centralAudioStream = await navigator.mediaDevices.getUserMedia({ audio: true });

        mediaRecorderCentral = new MediaRecorder(centralAudioStream);
        const audioChunks = [];

        mediaRecorderCentral.ondataavailable = event => {
            audioChunks.push(event.data);
        };

        mediaRecorderCentral.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            await sendAudioToConductors(audioBlob);
        };

        mediaRecorderCentral.start();
        console.log('✅ Grabación iniciada');

    } catch (error) {
        console.error('❌ Error iniciando grabación:', error);
        updateStatus('Error en grabación', 'error');

        // Restaurar botón
        const btn = safeGetElement('record-audio-btn');
        if (btn && btn.style) {
            btn.style.backgroundColor = '';
        }
    }
}

// Detener grabación
function stopRecording() {
    console.log('🎤 Deteniendo grabación...');

    try {
        if (mediaRecorderCentral && mediaRecorderCentral.state !== 'inactive') {
            mediaRecorderCentral.stop();
        }

        if (centralAudioStream) {
            centralAudioStream.getTracks().forEach(track => track.stop());
        }

        // Restaurar estado
        updateStatus('Listo', 'connected');

        // Restaurar botón
        const btn = safeGetElement('record-audio-btn');
        if (btn && btn.style) {
            btn.style.backgroundColor = '';
        }

        console.log('✅ Grabación detenida');

    } catch (error) {
        console.error('❌ Error deteniendo grabación:', error);
    }
}

// Enviar audio a conductores
async function sendAudioToConductors(audioBlob) {
    try {
        console.log('📤 Enviando audio a conductores...');

        // Convertir a base64
        const reader = new FileReader();
        reader.onload = function () {
            const base64Audio = reader.result.split(',')[1];

            // Enviar por WebSocket
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({
                    'type': 'central_audio',
                    'audio_data': base64Audio,
                    'room_name': roomName
                }));

                console.log('✅ Audio enviado');
                updateAudioLog('Audio enviado a conductores');
            } else {
                console.warn('⚠️ WebSocket no disponible');
            }
        };

        reader.readAsDataURL(audioBlob);

    } catch (error) {
        console.error('❌ Error enviando audio:', error);
    }
}

// Agregar audio a la cola de reproducción
function addAudioToQueue(audioData) {
    audioQueue.push(audioData);
    console.log('📋 Audio agregado a cola, total:', audioQueue.length);

    if (!isPlayingAudio) {
        playNextAudio();
    }
}

// Reproducir siguiente audio
async function playNextAudio() {
    if (audioQueue.length === 0) {
        isPlayingAudio = false;
        return;
    }

    isPlayingAudio = true;
    const audioData = audioQueue.shift();

    try {
        console.log('🔊 Reproduciendo audio...');

        // Crear elemento de audio
        const audioPlayer = safeGetElement('audio-player');
        if (!audioPlayer) {
            console.error('❌ Reproductor de audio no encontrado');
            return;
        }

        // Configurar audio
        audioPlayer.src = `data:audio/wav;base64,${audioData.audioData}`;

        // Eventos de reproducción
        audioPlayer.onended = () => {
            console.log('✅ Audio terminado');
            isPlayingAudio = false;
            playNextAudio(); // Reproducir siguiente
        };

        audioPlayer.onerror = (error) => {
            console.error('❌ Error reproduciendo audio:', error);
            isPlayingAudio = false;
            playNextAudio(); // Continuar con siguiente
        };

        // Reproducir
        await audioPlayer.play();

    } catch (error) {
        console.error('❌ Error en reproducción:', error);
        isPlayingAudio = false;
        playNextAudio(); // Continuar con siguiente
    }
}

// Actualizar log de audio
function updateAudioLog(message) {
    try {
        const audioLog = document.getElementById('audio-log');
        if (!audioLog) {
            console.warn('⚠️ audio-log no encontrado');
            return;
        }

        // Eliminar placeholder si existe
        const placeholder = audioLog.querySelector('.audio-log-empty');
        if (placeholder) {
            placeholder.remove();
        }

        // Crear entrada de log
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const logEntry = document.createElement('div');
        logEntry.className = 'audio-log-entry';
        logEntry.style.cssText = 'padding: 8px 12px; margin-bottom: 5px; background: rgba(255,255,255,0.05); border-left: 3px solid #4CAF50; border-radius: 4px; font-size: 0.9rem;';
        logEntry.innerHTML = `<span style="color: #888;">[${timestamp}]</span> ${message}`;

        // Agregar al inicio del log
        audioLog.insertBefore(logEntry, audioLog.firstChild);

        // Mantener solo las últimas 50 entradas
        const entries = audioLog.querySelectorAll('.audio-log-entry');
        if (entries.length > 50) {
            entries[entries.length - 1].remove();
        }

        console.log('✅ Log de audio actualizado:', message);
    } catch (error) {
        console.error('❌ Error actualizando log:', error);
    }
}

// Configurar eventos de click en la lista de conductores
function setupDriverListEvents() {
    console.log('🔧 Configurando eventos de la lista de conductores...');

    const driverItems = document.querySelectorAll('.user-item[data-driver-id]');
    console.log(`📋 Encontrados ${driverItems.length} elementos de conductor`);

    driverItems.forEach(item => {
        const driverId = item.getAttribute('data-driver-id');
        const driverName = item.getAttribute('data-driver-name') ||
            item.querySelector('span')?.textContent ||
            `Conductor #${driverId}`;

        // Remover eventos anteriores
        item.replaceWith(item.cloneNode(true));
        const newItem = document.querySelector(`[data-driver-id="${driverId}"]`);

        if (newItem) {
            newItem.addEventListener('click', function () {
                console.log(`💬 Click en conductor: ${driverName} (ID: ${driverId})`);
                openDriverChatFromList(driverId, driverName);
            });

            // Estilo cursor
            newItem.style.cursor = 'pointer';

            console.log(`✅ Evento configurado para conductor: ${driverName}`);
        }
    });
}

// Inicialización principal
async function initSystem() {
    if (systemInitialized) {
        console.log('⚠️ Sistema ya inicializado');
        return;
    }

    console.log('� Iniciando sistema completo...');

    try {
        // Asegurar elementos requeridos
        ensureRequiredElements();

        // Inicializar componentes
        updateStatus('Inicializando...', 'connecting');

        // Cargar Google Maps
        await loadGoogleMapsAPI();

        // Configurar WebSocket
        setupWebSocket();

        // Configurar sistema de audio
        setupAudioSystem();

        // Configurar eventos de la lista de conductores
        setupDriverListEvents();

        systemInitialized = true;
        updateStatus('Sistema listo', 'connected');
        console.log('✅ Sistema inicializado completamente');

    } catch (error) {
        console.error('❌ Error inicializando sistema:', error);
        updateStatus('Error en inicialización', 'error');
    }
}

// Función específica para abrir chat desde la lista lateral
function openDriverChatFromList(driverId, driverName) {
    // LOG MUY VISIBLE PARA VERIFICAR QUE SE EJECUTA LA VERSIÓN CORRECTA
    console.log('🚨🚨🚨 VERSIÓN NUEVA DE openDriverChatFromList EJECUTÁNDOSE 🚨🚨🚨');
    console.log('💬 ========================================');
    console.log('💬 Abriendo chat desde lista lateral:', driverName, 'ID:', driverId);
    console.log('💬 ========================================');
    console.log('🔍 DEBUG: Iniciando openDriverChatFromList...');
    console.log('🔍 DEBUG: driverId =', driverId, 'driverName =', driverName);
    console.log('🔍 DEBUG: Timestamp:', new Date().toISOString());

    try {
        // Buscar el elemento del conductor para obtener el historial pre-cargado
        console.log(`🔍 Buscando elemento del conductor con ID: ${driverId}...`);
        const driverElement = document.querySelector(`[data-driver-id="${driverId}"]`);
        console.log(`🔍 Elemento encontrado:`, driverElement);
        console.log(`🔍 Tipo de elemento:`, driverElement ? driverElement.constructor.name : 'null');
        
        let initialHistory = [];
        
        if (driverElement && driverElement.hasAttribute('data-initial-history')) {
            try {
                const historyJson = driverElement.getAttribute('data-initial-history');
                console.log(`📦 JSON crudo del historial:`, historyJson);
                console.log(`📦 Longitud del JSON:`, historyJson ? historyJson.length : 0);
                
                initialHistory = JSON.parse(historyJson);
                console.log(`📦 Historial parseado:`, initialHistory);
                console.log(`📦 Historial pre-cargado encontrado: ${initialHistory.length} mensajes`);
                
                if (initialHistory.length > 0) {
                    console.log(`📦 Primer mensaje:`, initialHistory[0]);
                    console.log(`📦 Último mensaje:`, initialHistory[initialHistory.length - 1]);
                }
                
                // Guardar el historial pre-cargado en localStorage para uso inmediato
                if (initialHistory.length > 0) {
                    saveChatHistoryToStorage(driverId, initialHistory);
                    console.log(`💾 Historial pre-cargado guardado en localStorage`);
                }
            } catch (e) {
                console.error('❌ Error parseando historial pre-cargado:', e);
                console.error('❌ JSON que causó el error:', driverElement.getAttribute('data-initial-history'));
            }
        } else {
            console.warn(`⚠️ No se encontró data-initial-history para conductor ${driverId}`);
            if (driverElement) {
                console.warn(`⚠️ Atributos del elemento:`, Array.from(driverElement.attributes).map(a => `${a.name}="${a.value.substring(0, 50)}..."`));
            }
        }
        
        // Actualizar el header del chat
        const chatHeader = document.getElementById('chat-header');
        if (chatHeader) {
            chatHeader.innerHTML = `
                <span>💬 Chat con: ${driverName}</span>
                <div class="header-controls">
                    <button class="header-toggle-btn" id="toggle-fullscreen" onclick="toggleFullscreen()" title="Pantalla completa (F11)">🔳</button>
                    <button class="header-toggle-btn minimize" onclick="toggleChat()" title="Ocultar chat (Ctrl+H)">✕</button>
                </div>
            `;
        }

        // RENDERIZAR HISTORIAL DIRECTAMENTE EN EL HTML (igual que comunicacion_driver.html)
        // Esto es más confiable que hacer llamadas al servidor
        const chatLog = document.getElementById('chat-log');
        if (!chatLog) {
            console.warn('⚠️ chat-log no encontrado');
            return;
        }
        
        // Limpiar el chat log completamente
        chatLog.innerHTML = '';
        console.log('🧹 chat-log limpiado');

        // Ocultar el mensaje de "no chat seleccionado"
        const noChatSelected = document.getElementById('no-chat-selected');
        if (noChatSelected) {
            noChatSelected.style.display = 'none';
            noChatSelected.style.visibility = 'hidden';
            noChatSelected.style.opacity = '0';
        }

        // Renderizar historial directamente desde data-initial-history (igual que el conductor)
        console.log(`🔍 Verificando historial: initialHistory =`, initialHistory);
        console.log(`🔍 Tipo:`, typeof initialHistory, Array.isArray(initialHistory));
        console.log(`🔍 Longitud:`, initialHistory ? initialHistory.length : 0);
        
        if (initialHistory && Array.isArray(initialHistory) && initialHistory.length > 0) {
            console.log(`📦 Renderizando ${initialHistory.length} mensajes directamente en el HTML (igual que el conductor)...`);
            console.log(`📦 chatLog antes de renderizar:`, chatLog);
            console.log(`📦 chatLog.innerHTML.length antes:`, chatLog.innerHTML.length);
            
            // Guardar en localStorage para consistencia
            saveChatHistoryToStorage(driverId, initialHistory);
            
            // Renderizar mensajes directamente en el HTML (igual que comunicacion_driver.html)
            let messagesRendered = 0;
            initialHistory.forEach((msg, index) => {
                try {
                    const isSent = msg.is_sent === true || msg.sender_id == 1;
                    const timestamp = typeof msg.timestamp === 'string'
                        ? (msg.timestamp.includes('T') ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : msg.timestamp)
                        : new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${isSent ? 'sent' : 'received'}`;
                    messageDiv.style.cssText = 'display: block !important; visibility: visible !important; opacity: 1 !important; margin-bottom: 10px; padding: 8px 12px; background: ' + (isSent ? '#007bff' : '#e9ecef') + '; color: ' + (isSent ? 'white' : 'black') + '; border-radius: 8px; max-width: 70%; ' + (isSent ? 'margin-left: auto;' : 'margin-right: auto;') + '; position: relative; z-index: 2;';
                    
                    messageDiv.innerHTML = `
                        <div style="font-weight: bold; margin-bottom: 4px; display: block;">${isSent ? 'Central' : (msg.sender_name || 'Desconocido')}</div>
                        <div style="display: block; word-wrap: break-word;">${msg.message || '(sin mensaje)'}</div>
                        <div class="message-time" style="font-size: 0.8em; opacity: 0.8; margin-top: 4px; display: block;">${timestamp}</div>
                    `;
                    
                    chatLog.appendChild(messageDiv);
                    messagesRendered++;
                    
                    if (index === 0 || index === initialHistory.length - 1) {
                        console.log(`   📝 Mensaje ${index + 1}/${initialHistory.length} renderizado:`, msg.message ? msg.message.substring(0, 30) : 'SIN MENSAJE');
                    }
                } catch (e) {
                    console.error(`❌ Error renderizando mensaje ${index + 1}:`, e, msg);
                }
            });
            
            // Scroll al final
            chatLog.scrollTop = chatLog.scrollHeight;
            
            // Verificar que los mensajes se agregaron
            const renderedMessages = chatLog.querySelectorAll('.message');
            console.log(`✅ ${messagesRendered} mensajes renderizados. Total en DOM: ${renderedMessages.length}`);
            console.log(`📦 chatLog.innerHTML.length después:`, chatLog.innerHTML.length);
            console.log(`📦 chatLog.children.length:`, chatLog.children.length);
            
            if (renderedMessages.length === 0 && initialHistory.length > 0) {
                console.error(`❌ ERROR: Se intentaron renderizar ${initialHistory.length} mensajes pero 0 aparecieron en el DOM!`);
                console.error(`   chatLog:`, chatLog);
                console.error(`   chatLog.style:`, chatLog.style.cssText);
            }
        } else {
            console.log('📭 No hay historial pre-cargado en data-initial-history');
            console.log(`   initialHistory es:`, initialHistory);
            console.log(`   Es array:`, Array.isArray(initialHistory));
            console.log(`   Longitud:`, initialHistory ? initialHistory.length : 'N/A');
            
            // Mostrar mensaje de "sin mensajes" si no hay historial
            chatLog.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #7f8c8d; display: block !important; visibility: visible !important;">
                    <strong>💬 No hay mensajes aún</strong><br>
                    <small>Inicia la conversación con ${driverName}</small>
                </div>
            `;
        }

        // Mostrar el área de entrada de mensaje
        const inputContainer = document.getElementById('chat-input-container');
        if (inputContainer) {
            inputContainer.style.display = 'flex';
        }

        // Configurar el input para este conductor
        const messageInput = document.getElementById('chat-message-input');
        if (messageInput) {
            messageInput.setAttribute('data-driver-id', driverId);
            messageInput.placeholder = `Escribe un mensaje a ${driverName}...`;
            messageInput.focus();
        }

        // Configurar el botón de envío - clonar para remover eventos anteriores
        const submitButton = document.getElementById('chat-message-submit');
        if (submitButton) {
            const newSubmitButton = submitButton.cloneNode(true);
            submitButton.parentNode.replaceChild(newSubmitButton, submitButton);

            newSubmitButton.addEventListener('click', function () {
                sendMessageToDriver(driverId);
            });
        }

        // Configurar Enter en el input - clonar para remover eventos anteriores
        if (messageInput) {
            const newInput = messageInput.cloneNode(true);
            messageInput.parentNode.replaceChild(newInput, messageInput);

            newInput.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') {
                    sendMessageToDriver(driverId);
                }
            });
        }

        // Hacer visible el chat window si está oculto
        const chatWindow = document.querySelector('.chat-window');
        if (chatWindow) {
            chatWindow.classList.remove('hidden');
        }
        
        // Guardar el ID del conductor actual para guardar mensajes recibidos
        const previousDriverId = currentChatDriverId;
        currentChatDriverId = driverId;

        // Resaltar el elemento seleccionado
        document.querySelectorAll('.user-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-driver-id="${driverId}"]`)?.classList.add('active');

        console.log(`✅ Chat iniciado desde lista: ${driverName} (ID: ${driverId})`);
        console.log(`📋 Conductor anterior: ${previousDriverId}, Conductor actual: ${driverId}`);
        
        // SIEMPRE cargar el historial desde el servidor para asegurar que se muestre
        // Esto es crítico porque el historial debe estar visible
        console.log(`🔄 Cargando historial para conductor ${driverId}...`);
        console.log(`🔄 Llamando loadChatHistory(${driverId})...`);
        
        // Cargar inmediatamente (sin esperar) - FORZAR ejecución
        try {
            const historyPromise = loadChatHistory(driverId);
            if (historyPromise && typeof historyPromise.then === 'function') {
                historyPromise.catch(error => {
                    console.error('❌ Error cargando historial:', error);
                    // Si falla, intentar desde localStorage como respaldo
                    try {
                        const storedMessages = loadChatHistoryFromStorage(driverId);
                        if (storedMessages && storedMessages.length > 0) {
                            console.log(`📂 Cargando ${storedMessages.length} mensajes desde localStorage como respaldo...`);
                            renderMessages(storedMessages);
                        } else {
                            console.log(`📭 No hay mensajes en localStorage`);
                        }
                    } catch (e) {
                        console.error('❌ Error cargando desde localStorage:', e);
                    }
                });
            } else {
                console.warn('⚠️ loadChatHistory no devolvió una promesa');
            }
        } catch (e) {
            console.error('❌ Error llamando loadChatHistory:', e);
            // Intentar desde localStorage como último recurso
            try {
                const storedMessages = loadChatHistoryFromStorage(driverId);
                if (storedMessages && storedMessages.length > 0) {
                    console.log(`📂 Cargando ${storedMessages.length} mensajes desde localStorage como último recurso...`);
                    renderMessages(storedMessages);
                }
            } catch (e2) {
                console.error('❌ Error cargando desde localStorage:', e2);
            }
        }

    } catch (error) {
        console.error('❌ Error abriendo chat desde lista:', error);
        alert('Error abriendo el chat. Por favor, intenta de nuevo.');
    }
}

// Inicialización cuando DOM esté listo
document.addEventListener('DOMContentLoaded', function () {
    console.log('🚀 DOM LISTO - Iniciando sistema completo...');

    // Pequeña pausa para asegurar que todo esté cargado
    setTimeout(() => {
        initSystem();
    }, 500);
});

// Exponer funciones globales
window.openDriverChat = openDriverChat;
window.sendChatMessage = sendChatMessage;

console.log('📝 comunicacion-completa.js cargado completamente');