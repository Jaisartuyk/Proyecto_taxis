// =====================================================
// SISTEMA WALKIE-TALKIE COMPLETO - VERSIÓN CORREGIDA
// =====================================================
console.log('🚀 LOADING comunicacion-completa.js - VERSIÓN COMPLETA CORREGIDA');
console.log('📅 Timestamp de carga:', new Date().toISOString());

// Variables globales
let map;
let socket;
let driverMarkers = {};
let audioContext;
let audioQueue = [];
let isPlayingAudio = false;
let mediaRecorderCentral;
let centralAudioStream;
let Maps_API_KEY;

// Variables de reconexión WebSocket
let wsReconnectAttempts = 0;
let wsMaxReconnectAttempts = 10;
let wsReconnectInterval = 1000;
let wsReconnectTimeout;

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
            setTimeout(() => {}, 100);
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
        script.onerror = function() {
            console.error('❌ Error cargando Google Maps API');
        };
        document.head.appendChild(script);
        
    } catch (error) {
        console.error('❌ Error configurando Google Maps:', error);
    }
}

// Función global para inicializar Google Maps
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
                        <div>
                            <h5>${taxi.nombre_conductor || 'Sin nombre'}</h5>
                            <p><strong>Placa:</strong> ${taxi.placa || 'N/A'}</p>
                            <p><strong>Estado:</strong> ${taxi.disponible ? 'Disponible' : 'Ocupado'}</p>
                            <p><strong>Teléfono:</strong> ${taxi.telefono || 'N/A'}</p>
                            <button onclick="openDriverChat(${taxi.id})" class="btn btn-primary btn-sm">
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
        const chatLog = document.getElementById('chat-log');
        if (chatLog) {
            chatLog.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #7f8c8d; border-bottom: 1px solid #eee;">
                    <strong>Iniciando chat con ${driverName}</strong><br>
                    <small>Los mensajes aparecerán aquí...</small>
                </div>
            `;
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
            
            newSubmitButton.addEventListener('click', function() {
                sendMessageToDriver(driverId);
            });
        }
        
        // Configurar Enter en el input
        if (messageInput) {
            messageInput.replaceWith(messageInput.cloneNode(true));
            const newInput = document.getElementById('chat-message-input');
            
            newInput.addEventListener('keypress', function(e) {
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
        
        console.log(`✅ Chat iniciado con ${driverName} (ID: ${driverId})`);
        
    } catch (error) {
        console.error('❌ Error abriendo chat:', error);
        alert('Error abriendo el chat. Por favor, intenta de nuevo.');
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
        // Agregar mensaje al chat log inmediatamente
        const chatLog = document.getElementById('chat-log');
        if (chatLog) {
            const timestamp = new Date().toLocaleTimeString();
            const messageHtml = `
                <div class="message outgoing" style="margin-bottom: 10px; padding: 8px 12px; background: #007bff; color: white; border-radius: 8px; max-width: 70%; margin-left: auto;">
                    <strong>Central:</strong> ${message}
                    <div style="font-size: 0.8em; opacity: 0.8;">${timestamp}</div>
                </div>
            `;
            chatLog.insertAdjacentHTML('beforeend', messageHtml);
            chatLog.scrollTop = chatLog.scrollHeight;
        }
        
        // Enviar por WebSocket
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                'type': 'chat_message',
                'driver_id': driverId,
                'message': message,
                'sender': 'central',
                'timestamp': new Date().toISOString()
            }));
            
            console.log('✅ Mensaje enviado por WebSocket');
        } else {
            console.warn('⚠️ WebSocket no disponible - mensaje no enviado');
            
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

// Configurar WebSocket
function setupWebSocket() {
    try {
        const wsPath = wsProtocol + window.location.host + '/ws/audio/conductores/';
        console.log('🔗 Conectando WebSocket:', wsPath);
        
        socket = new WebSocket(wsPath);
        
        socket.onopen = function(e) {
            console.log('✅ WebSocket conectado');
            updateStatus('Conectado al sistema', 'connected');
            wsReconnectAttempts = 0;
        };
        
        socket.onmessage = function(e) {
            console.log('📨 Mensaje WebSocket recibido');
            try {
                const data = JSON.parse(e.data);
                handleWebSocketMessage(data);
            } catch (error) {
                console.warn('⚠️ Error procesando mensaje:', error);
            }
        };
        
        socket.onclose = function(e) {
            console.log('❌ WebSocket desconectado, código:', e.code);
            updateStatus('Desconectado', 'disconnected');
            
            // Intentar reconexión automática
            if (wsReconnectAttempts < wsMaxReconnectAttempts) {
                wsReconnectAttempts++;
                console.log(`🔄 Reintentando conexión (${wsReconnectAttempts}/${wsMaxReconnectAttempts})...`);
                wsReconnectTimeout = setTimeout(() => {
                    setupWebSocket();
                }, wsReconnectInterval * wsReconnectAttempts);
            }
        };
        
        socket.onerror = function(error) {
            console.warn('⚠️ Error WebSocket:', error);
        };
        
    } catch (error) {
        console.error('❌ Error configurando WebSocket:', error);
    }
}

// Manejar mensajes WebSocket
function handleWebSocketMessage(data) {
    console.log('📨 Procesando mensaje:', data.type);
    
    switch (data.type) {
        case 'audio_message':
            handleAudioMessage(data);
            break;
        case 'chat_message':
            handleChatMessage(data);
            break;
        case 'driver_status':
            handleDriverStatusUpdate(data);
            break;
        case 'location_update':
            handleLocationUpdate(data);
            break;
        default:
            console.log('ℹ️ Tipo de mensaje no manejado:', data.type);
    }
}

// Manejar mensaje de audio
function handleAudioMessage(data) {
    console.log('🎵 Mensaje de audio recibido');
    
    try {
        if (data.audio_data && data.driver_id) {
            // Agregar a la cola de audio
            addAudioToQueue({
                audioData: data.audio_data,
                driverId: data.driver_id,
                timestamp: new Date().toISOString(),
                id: Date.now()
            });
            
            // Actualizar log de audio
            updateAudioLog(`Audio de Conductor #${data.driver_id}`);
        }
    } catch (error) {
        console.error('❌ Error procesando audio:', error);
    }
}

// Manejar mensaje de chat
function handleChatMessage(data) {
    console.log('💬 Mensaje de chat recibido de conductor:', data.driver_id);
    
    try {
        const chatLog = document.getElementById('chat-log');
        if (chatLog && data.message && data.driver_id) {
            // Verificar si tenemos el nombre del conductor
            const driverElement = document.querySelector(`[data-driver-id="${data.driver_id}"]`);
            let driverName = `Conductor #${data.driver_id}`;
            
            if (driverElement) {
                const nameElement = driverElement.querySelector('span');
                if (nameElement) {
                    driverName = nameElement.textContent;
                }
            }
            
            const timestamp = new Date().toLocaleTimeString();
            const messageHtml = `
                <div class="message incoming" style="margin-bottom: 10px; padding: 8px 12px; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; max-width: 70%;">
                    <strong>${driverName}:</strong> ${data.message}
                    <div style="font-size: 0.8em; color: #6c757d;">${timestamp}</div>
                </div>
            `;
            chatLog.insertAdjacentHTML('beforeend', messageHtml);
            chatLog.scrollTop = chatLog.scrollHeight;
            
            // Si el chat está oculto, mostrar notificación visual
            const chatWindow = document.querySelector('.chat-window');
            if (chatWindow && chatWindow.classList.contains('hidden')) {
                // Parpadeo del botón flotante de chat
                const floatingChatBtn = document.getElementById('floating-chat-btn');
                if (floatingChatBtn) {
                    floatingChatBtn.style.animation = 'pulse 1s infinite';
                    setTimeout(() => {
                        floatingChatBtn.style.animation = '';
                    }, 3000);
                }
                
                // Notificación opcional
                console.log(`💬 Nuevo mensaje de ${driverName}: ${data.message}`);
            }
        }
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
        reader.onload = function() {
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
        const audioLog = safeGetElement('audio-log');
        if (audioLog) {
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = `[${timestamp}] ${message}\n`;
            
            if (audioLog.tagName === 'TEXTAREA') {
                audioLog.value = logEntry + audioLog.value;
            } else {
                audioLog.textContent = logEntry + audioLog.textContent;
            }
            
            // Mantener solo las últimas 50 líneas
            const lines = audioLog.textContent.split('\n');
            if (lines.length > 50) {
                audioLog.textContent = lines.slice(0, 50).join('\n');
            }
        }
    } catch (error) {
        console.warn('⚠️ Error actualizando log:', error);
    }
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
    console.log('💬 Abriendo chat desde lista lateral:', driverName, 'ID:', driverId);
    
    try {
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
        const chatLog = document.getElementById('chat-log');
        if (chatLog) {
            chatLog.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #7f8c8d; border-bottom: 1px solid #eee;">
                    <strong>💬 Chat iniciado con ${driverName}</strong><br>
                    <small>Los mensajes aparecerán aquí en tiempo real...</small>
                </div>
            `;
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
        
        // Configurar el botón de envío - clonar para remover eventos anteriores
        const submitButton = document.getElementById('chat-message-submit');
        if (submitButton) {
            const newSubmitButton = submitButton.cloneNode(true);
            submitButton.parentNode.replaceChild(newSubmitButton, submitButton);
            
            newSubmitButton.addEventListener('click', function() {
                sendMessageToDriver(driverId);
            });
        }
        
        // Configurar Enter en el input - clonar para remover eventos anteriores
        if (messageInput) {
            const newInput = messageInput.cloneNode(true);
            messageInput.parentNode.replaceChild(newInput, messageInput);
            
            newInput.addEventListener('keypress', function(e) {
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
        
        // Resaltar el elemento seleccionado
        document.querySelectorAll('.user-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-driver-id="${driverId}"]`)?.classList.add('active');
        
        console.log(`✅ Chat iniciado desde lista: ${driverName} (ID: ${driverId})`);
        
    } catch (error) {
        console.error('❌ Error abriendo chat desde lista:', error);
        alert('Error abriendo el chat. Por favor, intenta de nuevo.');
    }
}

// Inicialización cuando DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
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