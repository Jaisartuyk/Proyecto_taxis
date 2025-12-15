// ========================================
// VERIFICAR SI ESTAMOS EN LA VISTA DE COMUNICACIÓN
// ========================================
// Este script solo debe ejecutarse en /central-comunicacion/
if (!window.location.pathname.includes('/central-comunicacion/') && 
    !window.location.pathname.includes('/comunicacion/')) {
    console.log('⏭️ comunicacion.js: No estamos en vista de comunicación, saltando inicialización');
    // No ejecutar el resto del script
} else {
    console.log('✅ comunicacion.js: Inicializando en vista de comunicación');

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
let currentPlayingAudio = null; // Para poder detener audio actual

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
    if (!statusDiv) return; // Verificar si el elemento existe
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
        clearMediaSession(); // Limpiar Media Session cuando no hay audio
        return;
    }

    isPlayingAudio = true;
    const base64Audio = audioQueue.shift();
    const audioPlayer = document.getElementById('audioPlayer');

    const audioBlob = base64ToBlob(base64Audio, 'audio/webm');
    const audioUrl = URL.createObjectURL(audioBlob);

    audioPlayer.src = audioUrl;
    
    // Configurar Media Session ANTES de reproducir
    setupMediaSession(audioPlayer, 'Central de Taxis');
    
    audioPlayer.play()
        .then(() => {
            console.log('✅ Reproduciendo audio con Media Session activa');
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
            console.log(`🚨 HAY ${pendingAudioQueue.length} AUDIOS PENDIENTES - Mostrando banner`);
            showPendingAudioIndicator();
            
            // Opcional: Reproducir automáticamente los audios pendientes
            // (descomenta la siguiente línea si quieres reproducción automática al regresar)
            // setTimeout(() => playPendingAudios(), 2000);
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
                
            case 'PLAY_AUDIO_IMMEDIATELY':
                // REPRODUCIR AUDIO INMEDIATAMENTE - FUNCIONALIDAD CLAVE
                playAudioImmediately(payload.audioUrl, payload.senderName, payload.volume || 1.0);
                break;
                
            case 'STOP_AUDIO':
                // DETENER REPRODUCCIÓN DE AUDIO INMEDIATAMENTE
                stopAllAudio();
                break;
                
            case 'PUSH_RECEIVED':
                // Notificación recibida mientras la app está abierta
                console.log('📻 Push notification recibida:', payload);
                break;
        }
    });
}

/**
 * Reproducir audio inmediatamente sin agregarlo a cola (para background)
 */
function playAudioImmediately(audioUrl, senderName, volume = 1.0) {
    try {
        console.log(`🔊 REPRODUCCIÓN INMEDIATA: Audio de ${senderName}`);
        
        // Detener audio anterior si existe
        if (currentPlayingAudio) {
            currentPlayingAudio.pause();
            currentPlayingAudio = null;
        }
        
        // Crear elemento de audio
        const audioElement = new Audio();
        audioElement.src = audioUrl;
        audioElement.volume = volume;
        audioElement.preload = 'auto';
        
        // Guardar referencia para poder detenerlo
        currentPlayingAudio = audioElement;
        
        // Configurar para máximo volumen y prioridad
        if (audioElement.setSinkId) {
            // Usar el dispositivo de salida por defecto
            audioElement.setSinkId('default').catch(console.warn);
        }
        
        // Configurar Media Session para reproducción en segundo plano
        setupMediaSession(audioElement, senderName);
        
        // Reproducir inmediatamente
        const playPromise = audioElement.play();
        
        if (playPromise !== undefined) {
            playPromise
                .then(() => {
                    console.log(`✅ Audio de ${senderName} reproduciéndose correctamente`);
                    
                    // Mostrar indicador visual temporal
                    showAudioPlayingIndicator(senderName);
                    
                    // Log del audio recibido
                    logAudio(`🎧 Audio urgente de ${senderName} reproducido automáticamente`);
                })
                .catch(error => {
                    console.error('❌ Error reproduciendo audio inmediato:', error);
                    
                    // Si falla la reproducción automática, agregar a cola
                    console.log('🔄 Agregando a cola de reproducción como fallback');
                    audioQueue.push({
                        audioData: audioUrl,
                        sender: senderName,
                        timestamp: Date.now()
                    });
                    
                    if (!isPlayingAudio) {
                        processAudioQueue();
                    }
                });
        }
        
        // Limpiar cuando termine
        audioElement.addEventListener('ended', () => {
            hideAudioPlayingIndicator();
            currentPlayingAudio = null;
            URL.revokeObjectURL(audioUrl);
            console.log(`🏁 Audio de ${senderName} terminado`);
        });
        
        audioElement.addEventListener('error', (error) => {
            console.error(`❌ Error en audio de ${senderName}:`, error);
            hideAudioPlayingIndicator();
            currentPlayingAudio = null;
        });
        
    } catch (error) {
        console.error('❌ Error en playAudioImmediately:', error);
        
        // Fallback: agregar a cola normal
        audioQueue.push({
            audioData: audioUrl,
            sender: senderName,
            timestamp: Date.now()
        });
        
        if (!isPlayingAudio) {
            processAudioQueue();
        }
    }
}

/**
 * Detener toda reproducción de audio
 */
function stopAllAudio() {
    console.log('⏹️ Deteniendo toda reproducción de audio');
    
    // Detener audio actual si existe
    if (currentPlayingAudio) {
        currentPlayingAudio.pause();
        currentPlayingAudio = null;
        console.log('⏹️ Audio inmediato detenido');
    }
    
    // Limpiar cola de audio
    audioQueue = [];
    isPlayingAudio = false;
    
    // Ocultar indicador visual
    hideAudioPlayingIndicator();
    
    // Detener cualquier audio en reproducción normal
    const audioElements = document.querySelectorAll('audio');
    audioElements.forEach(audio => {
        audio.pause();
        audio.currentTime = 0;
    });
    
    console.log('⏹️ Toda reproducción de audio detenida');
}

/**
 * Mostrar indicador visual de audio reproduciéndose
 */
function showAudioPlayingIndicator(senderName) {
    // Remover indicador anterior si existe
    hideAudioPlayingIndicator();
    
    const indicator = document.createElement('div');
    indicator.id = 'audio-playing-indicator';
    indicator.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(45deg, #ff6b6b, #ee5a52);
        color: white;
        padding: 15px 20px;
        border-radius: 25px;
        box-shadow: 0 4px 20px rgba(255, 107, 107, 0.3);
        z-index: 10000;
        font-weight: bold;
        font-size: 14px;
        animation: audioIndicatorPulse 1.5s infinite;
        max-width: 300px;
    `;
    
    indicator.innerHTML = `
        <i class="fas fa-volume-up" style="margin-right: 8px; animation: spin 2s linear infinite;"></i>
        <strong>📻 ${senderName}</strong><br>
        <small>Reproduciendo audio...</small>
    `;
    
    // Agregar animación CSS
    if (!document.getElementById('audio-indicator-styles')) {
        const style = document.createElement('style');
        style.id = 'audio-indicator-styles';
        style.textContent = `
            @keyframes audioIndicatorPulse {
                0%, 100% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.05); opacity: 0.9; }
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(indicator);
    
    console.log(`👁️ Indicador visual mostrado para ${senderName}`);
}

/**
 * Ocultar indicador visual de audio
 */
function hideAudioPlayingIndicator() {
    const indicator = document.getElementById('audio-playing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// Cargar datos al inicializar
document.addEventListener('DOMContentLoaded', function() {
    loadPersistedAudioData();
    requestAudioPermissions();
    
    // Verificar si se abrió con parámetros de autoplay
    checkAutoplayParameters();
});

/**
 * Solicitar permisos para reproducción automática de audio
 */
async function requestAudioPermissions() {
    try {
        console.log('🎵 Solicitando permisos de audio...');
        
        // 1. Solicitar permisos de notificaciones
        if ('Notification' in window && Notification.permission === 'default') {
            const permission = await Notification.requestPermission();
            console.log(`🔔 Permisos de notificación: ${permission}`);
        }
        
        // 2. Crear contexto de audio para permitir autoplay
        if ('AudioContext' in window || 'webkitAudioContext' in window) {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (!audioContext) {
                audioContext = new AudioContextClass();
            }
            
            // Reanudar contexto si está suspendido
            if (audioContext.state === 'suspended') {
                await audioContext.resume();
                console.log('🎵 Contexto de audio activado');
            }
        }
        
        // 3. Mostrar aviso al usuario para interactuar y permitir autoplay
        showAudioPermissionRequest();
        
    } catch (error) {
        console.error('❌ Error solicitando permisos de audio:', error);
    }
}

/**
 * Mostrar solicitud de permisos de audio al usuario
 */
function showAudioPermissionRequest() {
    // No mostrar si ya se dio permiso anteriormente
    if (localStorage.getItem('walkie_audio_permission') === 'granted') {
        return;
    }
    
    const permissionBanner = document.createElement('div');
    permissionBanner.id = 'audio-permission-banner';
    permissionBanner.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        text-align: center;
        z-index: 10001;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        border-bottom: 3px solid #5a6fd8;
    `;
    
    permissionBanner.innerHTML = `
        <div style="max-width: 800px; margin: 0 auto;">
            <h4 style="margin: 0 0 10px 0; color: #fff;">
                🎵 Activar Audio Automático de Walkie-Talkie
            </h4>
            <p style="margin: 0 0 15px 0; opacity: 0.9;">
                Para recibir mensajes de audio automáticamente (como radio/boquitoki), 
                haga clic en "Activar" y permita la reproducción automática.
            </p>
            <button 
                onclick="enableAutoAudio()" 
                style="background: #4CAF50; color: white; border: none; padding: 12px 24px; border-radius: 25px; font-weight: bold; margin-right: 10px; cursor: pointer;"
            >
                🔊 Activar Audio Automático
            </button>
            <button 
                onclick="dismissAudioPermission()" 
                style="background: transparent; color: white; border: 2px solid rgba(255,255,255,0.5); padding: 10px 20px; border-radius: 20px; cursor: pointer;"
            >
                Después
            </button>
        </div>
    `;
    
    document.body.appendChild(permissionBanner);
    console.log('📢 Banner de permisos de audio mostrado');
}

/**
 * Activar audio automático (función global para el botón)
 */
window.enableAutoAudio = async function() {
    try {
        console.log('🎵 Usuario activando audio automático...');
        
        // 1. Crear y reproducir audio silencioso para desbloquear autoplay
        const silentAudio = new Audio();
        silentAudio.src = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwgBjGJ1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwgBjGJ1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwgBjGJ1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwgBjGJ1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwgBjGJ1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwgBjGJ1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwgBjGJ1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwgBjGJ1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwgBjGJ1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwgBjGJ1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwgBjGJ1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwgBjGJ1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwgBjGJ1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwgBjGJ1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwgBjGJ1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwgBjGJ';
        silentAudio.volume = 0.01; // Muy bajo pero audible
        silentAudio.loop = false;
        
        const playPromise = silentAudio.play();
        if (playPromise !== undefined) {
            await playPromise;
        }
        
        // 2. Activar contexto de audio si está disponible
        if (audioContext && audioContext.state === 'suspended') {
            await audioContext.resume();
        }
        
        // 3. Guardar permiso concedido
        localStorage.setItem('walkie_audio_permission', 'granted');
        localStorage.setItem('walkie_audio_enabled_date', new Date().toISOString());
        
        // 4. Ocultar banner
        const banner = document.getElementById('audio-permission-banner');
        if (banner) {
            banner.remove();
        }
        
        // 5. Mostrar confirmación
        showAudioEnabledConfirmation();
        
        console.log('✅ Audio automático activado correctamente');
        
    } catch (error) {
        console.error('❌ Error activando audio automático:', error);
        alert('Error activando audio automático. Por favor, recargue la página e intente nuevamente.');
    }
};

/**
 * Descartar solicitud de permisos temporalmente
 */
window.dismissAudioPermission = function() {
    const banner = document.getElementById('audio-permission-banner');
    if (banner) {
        banner.remove();
    }
    
    // Recordar que se descartó por esta sesión
    sessionStorage.setItem('audio_permission_dismissed', 'true');
    console.log('📋 Solicitud de audio descartada temporalmente');
};

/**
 * Mostrar confirmación de audio activado
 */
function showAudioEnabledConfirmation() {
    const confirmation = document.createElement('div');
    confirmation.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(45deg, #4CAF50, #45a049);
        color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(76, 175, 80, 0.3);
        z-index: 10002;
        max-width: 350px;
        animation: slideInRight 0.5s ease-out;
    `;
    
    confirmation.innerHTML = `
        <h4 style="margin: 0 0 10px 0;">🎵 ¡Audio Automático Activado!</h4>
        <p style="margin: 0; opacity: 0.9;">
            Ahora recibirás audios de walkie-talkie automáticamente, 
            incluso cuando la app esté en background.
        </p>
    `;
    
    document.body.appendChild(confirmation);
    
    // Auto-remover después de 5 segundos
    setTimeout(() => {
        if (confirmation.parentNode) {
            confirmation.remove();
        }
    }, 5000);
}

// ========================================
// MEDIA SESSION API - REPRODUCCIÓN EN SEGUNDO PLANO
// ========================================

/**
 * Configurar Media Session API para permitir reproducción en segundo plano
 * Esto permite que el audio continúe cuando:
 * - El usuario cambia de app
 * - El usuario bloquea la pantalla
 * - El usuario cambia de pestaña
 */
function setupMediaSession(audioElement, senderName = 'Central de Taxis') {
    // Verificar si Media Session API está disponible
    if (!('mediaSession' in navigator)) {
        console.log('⚠️ Media Session API no disponible en este navegador');
        return;
    }

    try {
        // Configurar metadata del audio actual
        navigator.mediaSession.metadata = new MediaMetadata({
            title: '🎤 Audio de Comunicación',
            artist: senderName,
            album: 'De Aquí Pa\'llá - Walkie Talkie',
            artwork: [
                { 
                    src: '/static/imagenes/icon-192x192.png', 
                    sizes: '192x192', 
                    type: 'image/png' 
                },
                { 
                    src: '/static/imagenes/icon-512x512.png', 
                    sizes: '512x512', 
                    type: 'image/png' 
                }
            ]
        });

        // Configurar handlers para controles de reproducción
        // Estos aparecerán en la barra de notificaciones y pantalla de bloqueo
        
        navigator.mediaSession.setActionHandler('play', () => {
            console.log('▶️ Media Session: Play solicitado');
            audioElement.play()
                .then(() => console.log('✅ Reproducción iniciada desde Media Session'))
                .catch(err => console.error('❌ Error al reproducir:', err));
        });

        navigator.mediaSession.setActionHandler('pause', () => {
            console.log('⏸️ Media Session: Pause solicitado');
            audioElement.pause();
        });

        // Algunos navegadores soportan estos controles adicionales
        try {
            navigator.mediaSession.setActionHandler('stop', () => {
                console.log('⏹️ Media Session: Stop solicitado');
                audioElement.pause();
                audioElement.currentTime = 0;
                clearMediaSession();
            });
        } catch (error) {
            console.log('⚠️ Action "stop" no soportada');
        }

        // Actualizar estado de reproducción
        navigator.mediaSession.playbackState = 'playing';
        
        console.log('✅ Media Session configurada correctamente para:', senderName);
        
    } catch (error) {
        console.error('❌ Error configurando Media Session:', error);
    }
}

/**
 * Limpiar Media Session cuando no hay audio reproduciéndose
 */
function clearMediaSession() {
    if (!('mediaSession' in navigator)) {
        return;
    }

    try {
        navigator.mediaSession.playbackState = 'none';
        navigator.mediaSession.metadata = null;
        
        // Limpiar handlers
        navigator.mediaSession.setActionHandler('play', null);
        navigator.mediaSession.setActionHandler('pause', null);
        
        try {
            navigator.mediaSession.setActionHandler('stop', null);
        } catch (error) {
            // Ignorar si no está soportado
        }
        
        console.log('🧹 Media Session limpiada');
    } catch (error) {
        console.error('❌ Error limpiando Media Session:', error);
    }
}

// ========================================
// LISTENER PARA MENSAJES DEL SERVICE WORKER
// ========================================

/**
 * Escuchar mensajes del Service Worker para reproducir audio inmediatamente
 * Esto permite que el audio se reproduzca cuando la app está en segundo plano
 */
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('message', (event) => {
        console.log('📨 Mensaje recibido del Service Worker:', event.data);
        
        if (event.data && event.data.type === 'PLAY_AUDIO_IMMEDIATELY') {
            const { audioUrl, senderName, timestamp } = event.data;
            
            console.log(`🔊 REPRODUCCIÓN INMEDIATA SOLICITADA por ${senderName}`);
            
            // Reproducir el audio inmediatamente
            if (audioUrl && senderName) {
                playAudioImmediately(audioUrl, senderName, 1.0);
                
                // Mostrar notificación visual en la app
                showAudioPlayingIndicator(senderName);
                
                // Log del evento
                logAudio(`🎧 Audio urgente de ${senderName} reproducido desde notificación push`);
            } else {
                console.error('❌ Datos de audio incompletos en mensaje del SW');
            }
        }
    });
    
    console.log('✅ Listener de Service Worker configurado para reproducción de audio');
}

// Limpiar audios antiguos cada 30 minutos
setInterval(cleanOldPendingAudios, 30 * 60 * 1000);

// ========================================
// AUTOPLAY DESDE URL PARAMETERS
// ========================================

/**
 * Verificar si la página se abrió con parámetros de autoplay
 * Esto sucede cuando el Service Worker abre la app automáticamente
 */
function checkAutoplayParameters() {
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const autoplay = urlParams.get('autoplay');
        const audioUrl = urlParams.get('audio');
        const senderName = urlParams.get('sender');
        const background = urlParams.get('background');
        
        console.log('🔍 Verificando parámetros de URL:', {
            autoplay,
            hasAudio: !!audioUrl,
            sender: senderName,
            background
        });
        
        if (autoplay === 'true' && audioUrl && senderName) {
            console.log('🎬 AUTOPLAY DETECTADO - Reproduciendo audio automáticamente');
            
            // Esperar un momento para que todo se inicialice
            setTimeout(() => {
                // Decodificar URL del audio
                const decodedAudioUrl = decodeURIComponent(audioUrl);
                const decodedSenderName = decodeURIComponent(senderName);
                
                console.log(`🔊 Reproduciendo: ${decodedSenderName}`);
                
                // Reproducir inmediatamente
                playAudioImmediately(decodedAudioUrl, decodedSenderName, 1.0);
                
                // Si es en background, no mostrar indicadores visuales
                if (background !== 'true') {
                    showAudioPlayingIndicator(decodedSenderName);
                }
                
                // Limpiar URL para que no se reproduzca de nuevo si recarga
                const cleanUrl = window.location.pathname;
                window.history.replaceState({}, document.title, cleanUrl);
                
                console.log('✅ Autoplay completado - URL limpiada');
            }, 500); // Esperar 500ms para que se inicialice todo
        }
    } catch (error) {
        console.error('❌ Error verificando parámetros de autoplay:', error);
    }
}

// Cerrar el bloque if/else de verificación de vista
}
