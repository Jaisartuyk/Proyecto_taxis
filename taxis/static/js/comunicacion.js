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

const roomName = "conductores";
const wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";

// Elementos del DOM
const startCentralMicBtn = document.getElementById('startCentralMic');
const stopCentralMicBtn = document.getElementById('stopCentralMic');

// Inicialización
async function init() {
    try {
        // Obtener API key de Google Maps de forma segura
        const response = await fetch('/api/maps-key/');
        const data = await response.json();
        Maps_API_KEY = data.maps_api_key;
        
        // Cargar Google Maps
        loadGoogleMapsAPI();
    } catch (error) {
        console.error('Error obteniendo API key:', error);
        updateStatus("Error de configuración", "disconnected");
    }
}

function loadGoogleMapsAPI() {
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${Maps_API_KEY}&callback=initMap`;
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
}

window.initMap = function () {
    const defaultLatLng = { lat: -2.170998, lng: -79.922359 };
    map = new google.maps.Map(document.getElementById("map"), {
        zoom: 14,
        center: defaultLatLng,
        mapTypeId: 'roadmap'
    });
    console.log("Mapa de Google Maps inicializado.");
    setupWebSocket();
    setupCentralAudioControls();
    
    // Iniciar actualización periódica de ubicaciones
    setInterval(fetchDriverLocations, 10000);
    fetchDriverLocations();
};

// Variables de reconexión
wsReconnectAttempts = 0;
wsMaxReconnectAttempts = 10;
wsReconnectInterval = 1000; // Inicio con 1 segundo
wsReconnectTimeout;

function setupWebSocket() {
    const host = window.location.host;
    
    // Limpiar timeout anterior si existe
    if (wsReconnectTimeout) {
        clearTimeout(wsReconnectTimeout);
        wsReconnectTimeout = null;
    }
    
    console.log(`📻 Intentando conexión WebSocket (intento ${wsReconnectAttempts + 1}/${wsMaxReconnectAttempts})...`);
    socket = new WebSocket(`${wsProtocol}${host}/ws/audio/${roomName}/`);

    socket.onopen = function(event) {
        console.log('✅ Conexión WebSocket abierta.');
        updateStatus("Conectado", "connected");
        logMessage("🔗 Conectado a la central de taxis.");
        
        // Resetear contador de intentos de reconexión
        wsReconnectAttempts = 0;
        wsReconnectInterval = 1000;
        
        if (mediaRecorderCentral) {
            startCentralMicBtn.disabled = false;
        }
    };

    socket.onmessage = function(event) {
        if (typeof event.data === "string") {
            const data = JSON.parse(event.data);
            console.log('📻 Mensaje de WebSocket recibido:', data);

            // Manejo de actualización de ubicación
            if (data.type === 'driver_location_update') {
                const driverId = data.driverId;
                const lat = data.latitude;
                const lng = data.longitude;

                if (lat && lng) {
                    updateDriverLocation(driverId, lat, lng);
                    logMessage(`📍 Ubicación de ${driverId}: Lat ${lat.toFixed(4)}, Lng ${lng.toFixed(4)}`);
                }
            } 
            // Manejo de mensajes de audio
            else if (data.type === 'audio_broadcast') {
                const senderId = data.senderId;
                const senderRole = data.senderRole;
                const audioBase64 = data.audio;

                // Reproducir audio de todos (Central y otros conductores)
                if (audioBase64) {
                    const displayName = senderRole === 'Central' ? '📡 Central' : `🚕 ${senderId}`;
                    logAudio(`🎧 Audio de ${displayName} recibido.`);
                    playAudioFromBase64(audioBase64);
                    
                    // Mostrar notificación si la ventana no está enfocada
                    if (window.notificationManager && document.hidden) {
                        window.notificationManager.notifyAudioMessage(displayName);
                    }
                }
            } 
            // Manejo de nuevas carreras
            else if (data.type === 'new_ride') {
                logMessage(`🚕 Nueva carrera: ${data.pickup} → ${data.destination}`);
                if (window.notificationManager) {
                    window.notificationManager.notifyNewRide(data);
                }
            }
            // Manejo de carrera aceptada
            else if (data.type === 'ride_accepted') {
                logMessage(`✅ Carrera aceptada por ${data.driverName}`);
                if (window.notificationManager) {
                    window.notificationManager.notifyRideAccepted(data);
                }
            }
            else {
                logMessage(`❓ Mensaje desconocido: ${JSON.stringify(data)}`);
            }
        }
    };

    socket.onclose = function(event) {
        console.log(`❌ Conexión WebSocket cerrada: Código ${event.code}, Razón: ${event.reason}`);
        updateStatus("Desconectado", "disconnected");
        startCentralMicBtn.disabled = true;
        stopCentralMicBtn.disabled = true;
        
        // Intentar reconexión automática con backoff exponencial
        if (wsReconnectAttempts < wsMaxReconnectAttempts) {
            wsReconnectAttempts++;
            const delay = Math.min(wsReconnectInterval * Math.pow(2, wsReconnectAttempts - 1), 30000); // Máximo 30 segundos
            
            logMessage(`🔄 Reconectando en ${delay/1000}s... (intento ${wsReconnectAttempts}/${wsMaxReconnectAttempts})`);
            
            wsReconnectTimeout = setTimeout(() => {
                setupWebSocket();
            }, delay);
        } else {
            logMessage(`❌ Máximo número de intentos alcanzado. Conexión fallida.`);
            updateStatus("Error Fatal", "error");
        }
    };

    socket.onerror = function(error) {
        console.error('❌ Error de WebSocket:', error);
        updateStatus("Error de Conexión", "disconnected");
        logMessage(`❌ Error de conexión WebSocket`);
    };
}

// Manejar cambios de visibilidad de la página
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        console.log('📱 App enviada al background');
    } else {
        console.log('📱 App regresó al foreground');
        
        // Verificar estado de conexión WebSocket cuando regrese al foreground
        if (!socket || socket.readyState === WebSocket.CLOSED) {
            console.log('🔄 Reconectando WebSocket después de regresar del background...');
            wsReconnectAttempts = 0; // Resetear contador para reconexión inmediata
            setupWebSocket();
        }
        
        // Cargar datos persistidos por si hubo cambios mientras estaba en background
        loadPersistedAudioData();
    }
});

// Función para obtener ubicaciones desde la API
async function fetchDriverLocations() {
    try {
        const response = await fetch('/api/taxis_ubicacion/');
        if (!response.ok) {
            logMessage('Error al obtener ubicaciones de la API.');
            return;
        }
        const taxis = await response.json();
        console.log('Ubicaciones recibidas de la API:', taxis);

        const activeTaxiIds = new Set();

        taxis.forEach(taxi => {
            if (taxi.lat && taxi.lng) {
                updateDriverLocation(taxi.id, taxi.lat, taxi.lng, taxi.nombre);
                activeTaxiIds.add(taxi.id.toString());
            }
        });

        // Limpiar marcadores inactivos
        for (const driverId in driverMarkers) {
            if (!activeTaxiIds.has(driverId)) {
                driverMarkers[driverId].setMap(null);
                delete driverMarkers[driverId];
                logMessage(`Conductor ${driverId} desconectado.`);
            }
        }
    } catch (error) {
        console.error('Error en fetchDriverLocations:', error);
        logMessage('Fallo la conexión con la API de ubicaciones.');
    }
}

// Funciones para el mapa
function updateDriverLocation(driverId, lat, lng, driverName = null) {
    const position = { lat: lat, lng: lng };

    if (driverMarkers[driverId]) {
        driverMarkers[driverId].setPosition(position);
    } else {
        const marker = new google.maps.Marker({
            position: position,
            map: map,
            title: driverName || `Conductor ${driverId}`,
            icon: {
                url: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'
            }
        });

        const infoWindow = new google.maps.InfoWindow({
            content: `<strong>${driverName || `Conductor ${driverId}`}</strong><br>Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}`
        });

        marker.addListener('click', function() {
            infoWindow.open(map, marker);
        });

        driverMarkers[driverId] = marker;
    }

    map.setCenter(position);
}

// Funciones de utilidad
function logMessage(msg) {
    const logDiv = document.getElementById('log');
    if (!logDiv) return; // Verificar si el elemento existe
    const p = document.createElement('p');
    p.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
    logDiv.appendChild(p);
    logDiv.scrollTop = logDiv.scrollHeight;
}

function logAudio(msg) {
    const audioLogDiv = document.getElementById('audioLog');
    if (!audioLogDiv) return; // Verificar si el elemento existe
    const p = document.createElement('p');
    p.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
    audioLogDiv.appendChild(p);
    audioLogDiv.scrollTop = audioLogDiv.scrollHeight;
}

function updateStatus(message, className) {
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = message;
    statusDiv.className = `status ${className}`;
}

// Funciones para grabar y enviar audio desde la Central
function setupCentralAudioControls() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            centralAudioStream = stream;
            mediaRecorderCentral = new MediaRecorder(stream);
            let audioChunks = [];

            mediaRecorderCentral.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorderCentral.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                audioChunks = [];

                const reader = new FileReader();
                reader.onloadend = () => {
                    const base64Audio = reader.result.split(',')[1];
                    if (socket && socket.readyState === WebSocket.OPEN) {
                        socket.send(JSON.stringify({
                            type: 'audio_message',
                            audio: base64Audio,
                            senderId: 'Central',
                            senderRole: 'Central'
                        }));
                        logAudio('🎤 Audio enviado a todos los conductores.');
                    } else {
                        logAudio('⚠️ No se pudo enviar el audio. WebSocket no está conectado.');
                    }
                };
                reader.readAsDataURL(audioBlob);
            };

            startCentralMicBtn.addEventListener('mousedown', () => {
                if (socket && socket.readyState === WebSocket.OPEN) {
                    mediaRecorderCentral.start();
                    logAudio('🎤 Grabando audio...');
                    startCentralMicBtn.style.backgroundColor = '#FF5722';
                }
            });

            startCentralMicBtn.addEventListener('mouseup', () => {
                if (mediaRecorderCentral.state === 'recording') {
                    mediaRecorderCentral.stop();
                    startCentralMicBtn.style.backgroundColor = '#007bff';
                }
            });

            startCentralMicBtn.addEventListener('mouseleave', () => {
                if (mediaRecorderCentral.state === 'recording') {
                    mediaRecorderCentral.stop();
                    startCentralMicBtn.style.backgroundColor = '#007bff';
                }
            });
        })
        .catch(error => {
            console.error('Error al acceder al micrófono:', error);
            logAudio('⚠️ No se pudo acceder al micrófono.');
            startCentralMicBtn.disabled = true;
        });
}

// Funciones para manejo y reproducción de audio
function playAudioFromBase64(base64String) {
    audioQueue.push(base64String);
    if (!isPlayingAudio) {
        processAudioQueue();
    }
}

function processAudioQueue() {
    if (audioQueue.length === 0) {
        isPlayingAudio = false;
        return;
    }

    isPlayingAudio = true;
    const base64Audio = audioQueue.shift();
    const audioPlayer = document.getElementById('audioPlayer');

    const audioBlob = base64ToBlob(base64Audio, 'audio/webm');
    const audioUrl = URL.createObjectURL(audioBlob);

    audioPlayer.src = audioUrl;
    audioPlayer.play()
        .then(() => {
            console.log('Reproduciendo audio...');
        })
        .catch(error => {
            console.error('Error al reproducir audio:', error);
            processAudioQueue();
        });

    audioPlayer.onended = () => {
        URL.revokeObjectURL(audioUrl);
        processAudioQueue();
    };
}

function base64ToBlob(base64, mimeType) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
}

// Iniciar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', init);

// ========================================
// SISTEMA DE GESTIÓN DE AUDIOS WALKIE-TALKIE
// ========================================

/**
 * Cola de audios pendientes para reproducir cuando el usuario abra la app
 */
pendingAudioQueue = [];
dismissedAudios = new Set();

/**
 * Guardar audio pendiente en localStorage
 */
function savePendingAudio(senderId, senderName, audioUrl, timestamp) {
    const audioId = `audio_${senderId}_${timestamp}`;
    
    // Evitar duplicados
    if (dismissedAudios.has(audioId)) {
        console.log('📻 Audio ya fue descartado:', audioId);
        return;
    }
    
    const pendingAudio = {
        id: audioId,
        senderId: senderId,
        senderName: senderName,
        audioUrl: audioUrl,
        timestamp: timestamp,
        received: Date.now()
    };
    
    // Agregar a la cola
    pendingAudioQueue.push(pendingAudio);
    
    // Guardar en localStorage
    localStorage.setItem('walkie_pending_audios', JSON.stringify(pendingAudioQueue));
    
    console.log(`📻 Audio pendiente guardado: ${senderName} - ${timestamp}`);
    
    // Mostrar indicador visual
    showPendingAudioIndicator();
}

/**
 * Marcar audio como descartado
 */
function markAudioAsDismissed(senderId, timestamp) {
    const audioId = `audio_${senderId}_${timestamp}`;
    
    // Agregar a la lista de descartados
    dismissedAudios.add(audioId);
    
    // Remover de la cola pendiente
    pendingAudioQueue = pendingAudioQueue.filter(audio => audio.id !== audioId);
    
    // Actualizar localStorage
    localStorage.setItem('walkie_pending_audios', JSON.stringify(pendingAudioQueue));
    localStorage.setItem('walkie_dismissed_audios', JSON.stringify([...dismissedAudios]));
    
    console.log(`📻 Audio marcado como descartado: ${audioId}`);
    
    // Actualizar indicador visual
    updatePendingAudioIndicator();
}

/**
 * Limpiar audios pendientes antiguos (más de 1 hora)
 */
function cleanOldPendingAudios(beforeTimestamp = null) {
    if (!beforeTimestamp) {
        beforeTimestamp = Date.now() - (60 * 60 * 1000); // 1 hora
    }
    
    const initialCount = pendingAudioQueue.length;
    
    // Filtrar audios antiguos
    pendingAudioQueue = pendingAudioQueue.filter(audio => audio.received > beforeTimestamp);
    
    // Limpiar audios descartados antiguos
    const oldDismissedIds = [...dismissedAudios].filter(audioId => {
        const timestamp = audioId.split('_')[2];
        return parseInt(timestamp) < beforeTimestamp;
    });
    
    oldDismissedIds.forEach(id => dismissedAudios.delete(id));
    
    // Actualizar localStorage
    localStorage.setItem('walkie_pending_audios', JSON.stringify(pendingAudioQueue));
    localStorage.setItem('walkie_dismissed_audios', JSON.stringify([...dismissedAudios]));
    
    const removedCount = initialCount - pendingAudioQueue.length;
    if (removedCount > 0) {
        console.log(`🧹 ${removedCount} audios antiguos limpiados`);
        updatePendingAudioIndicator();
    }
}

/**
 * Cargar datos persistidos al inicializar
 */
function loadPersistedAudioData() {
    try {
        // Cargar cola pendiente
        const savedQueue = localStorage.getItem('walkie_pending_audios');
        if (savedQueue) {
            pendingAudioQueue = JSON.parse(savedQueue);
        }
        
        // Cargar audios descartados
        const savedDismissed = localStorage.getItem('walkie_dismissed_audios');
        if (savedDismissed) {
            dismissedAudios = new Set(JSON.parse(savedDismissed));
        }
        
        // Limpiar audios antiguos al cargar
        cleanOldPendingAudios();
        
        console.log(`📻 Datos cargados: ${pendingAudioQueue.length} audios pendientes, ${dismissedAudios.size} descartados`);
        
        // Mostrar indicador si hay audios pendientes
        if (pendingAudioQueue.length > 0) {
            showPendingAudioIndicator();
        }
        
    } catch (error) {
        console.error('❌ Error cargando datos persistidos:', error);
        pendingAudioQueue = [];
        dismissedAudios = new Set();
    }
}

/**
 * Mostrar indicador de audios pendientes
 */
function showPendingAudioIndicator() {
    let indicator = document.getElementById('pending-audio-indicator');
    
    if (!indicator && pendingAudioQueue.length > 0) {
        indicator = document.createElement('div');
        indicator.id = 'pending-audio-indicator';
        indicator.innerHTML = `
            <div class="alert alert-warning d-flex align-items-center" role="alert">
                <i class="fas fa-volume-up me-2"></i>
                <div class="flex-grow-1">
                    <strong>📻 ${pendingAudioQueue.length} mensaje(s) de audio pendiente(s)</strong>
                    <br><small>Haga clic para reproducir los audios recibidos mientras estaba ausente</small>
                </div>
                <button type="button" class="btn btn-warning btn-sm me-2" onclick="playPendingAudios()">
                    <i class="fas fa-play"></i> Reproducir
                </button>
                <button type="button" class="btn btn-outline-secondary btn-sm" onclick="dismissAllPendingAudios()">
                    <i class="fas fa-times"></i> Descartar
                </button>
            </div>
        `;
        
        // Insertar al inicio del contenido principal
        const mainContent = document.querySelector('.container-fluid');
        if (mainContent && mainContent.firstChild) {
            mainContent.insertBefore(indicator, mainContent.firstChild);
        }
    }
    
    updatePendingAudioIndicator();
}

/**
 * Actualizar indicador de audios pendientes
 */
function updatePendingAudioIndicator() {
    const indicator = document.getElementById('pending-audio-indicator');
    
    if (pendingAudioQueue.length === 0) {
        if (indicator) {
            indicator.remove();
        }
    } else if (indicator) {
        const countElement = indicator.querySelector('strong');
        if (countElement) {
            countElement.textContent = `📻 ${pendingAudioQueue.length} mensaje(s) de audio pendiente(s)`;
        }
    }
}

/**
 * Reproducir todos los audios pendientes en secuencia
 */
function playPendingAudios() {
    if (pendingAudioQueue.length === 0) {
        console.log('📻 No hay audios pendientes para reproducir');
        return;
    }
    
    console.log(`📻 Iniciando reproducción de ${pendingAudioQueue.length} audios pendientes`);
    
    // Agregar todos los audios a la cola de reproducción
    pendingAudioQueue.forEach(pendingAudio => {
        audioQueue.push({
            audioData: pendingAudio.audioUrl,
            sender: pendingAudio.senderName,
            timestamp: pendingAudio.timestamp
        });
    });
    
    // Limpiar la cola pendiente
    pendingAudioQueue = [];
    localStorage.setItem('walkie_pending_audios', JSON.stringify(pendingAudioQueue));
    
    // Actualizar indicador
    updatePendingAudioIndicator();
    
    // Iniciar reproducción si no está en curso
    if (!isPlayingAudio) {
        processAudioQueue();
    }
    
    logMessage('📻 Reproduciendo audios pendientes...');
}

/**
 * Descartar todos los audios pendientes
 */
function dismissAllPendingAudios() {
    pendingAudioQueue.forEach(audio => {
        dismissedAudios.add(audio.id);
    });
    
    pendingAudioQueue = [];
    
    // Actualizar localStorage
    localStorage.setItem('walkie_pending_audios', JSON.stringify(pendingAudioQueue));
    localStorage.setItem('walkie_dismissed_audios', JSON.stringify([...dismissedAudios]));
    
    // Actualizar indicador
    updatePendingAudioIndicator();
    
    console.log('📻 Todos los audios pendientes han sido descartados');
    logMessage('📻 Audios pendientes descartados');
}

/**
 * Manejar mensajes del service worker
 */
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('message', function(event) {
        const { type, payload } = event.data;
        
        switch (type) {
            case 'SAVE_PENDING_AUDIO':
                savePendingAudio(
                    payload.senderId,
                    payload.senderName,
                    payload.audioUrl,
                    payload.timestamp
                );
                break;
                
            case 'DISMISS_AUDIO':
                markAudioAsDismissed(payload.senderId, payload.timestamp);
                break;
                
            case 'CLEAN_OLD_AUDIOS':
                cleanOldPendingAudios(payload.beforeTimestamp);
                break;
                
            case 'PUSH_RECEIVED':
                // Notificación recibida mientras la app está abierta
                console.log('📻 Push notification recibida:', payload);
                break;
        }
    });
}

// Cargar datos al inicializar
document.addEventListener('DOMContentLoaded', function() {
    loadPersistedAudioData();
});

// Limpiar audios antiguos cada 30 minutos
setInterval(cleanOldPendingAudios, 30 * 60 * 1000);
