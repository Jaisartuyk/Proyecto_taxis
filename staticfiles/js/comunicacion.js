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

function setupWebSocket() {
    const host = window.location.host;
    socket = new WebSocket(`${wsProtocol}${host}/ws/audio/${roomName}/`);

    socket.onopen = function(event) {
        console.log('Conexión WebSocket abierta.');
        updateStatus("Conectado", "connected");
        logMessage("Conectado a la central de taxis.");
        if (mediaRecorderCentral) {
            startCentralMicBtn.disabled = false;
        }
    };

    socket.onmessage = function(event) {
        if (typeof event.data === "string") {
            const data = JSON.parse(event.data);
            console.log('Mensaje de WebSocket recibido:', data);

            // Manejo de actualización de ubicación
            if (data.type === 'driver_location_update') {
                const driverId = data.driverId;
                const lat = data.latitude;
                const lng = data.longitude;

                if (lat && lng) {
                    updateDriverLocation(driverId, lat, lng);
                    logMessage(`Ubicación de ${driverId}: Lat ${lat.toFixed(4)}, Lng ${lng.toFixed(4)}`);
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
                logMessage(`Nueva carrera: ${data.pickup} → ${data.destination}`);
                if (window.notificationManager) {
                    window.notificationManager.notifyNewRide(data);
                }
            }
            // Manejo de carrera aceptada
            else if (data.type === 'ride_accepted') {
                logMessage(`Carrera aceptada por ${data.driverName}`);
                if (window.notificationManager) {
                    window.notificationManager.notifyRideAccepted(data);
                }
            }
            else {
                logMessage(`Mensaje desconocido: ${JSON.stringify(data)}`);
            }
        }
    };

    socket.onclose = function(event) {
        console.log('Conexión WebSocket cerrada:', event.code, event.reason);
        updateStatus("Desconectado", "disconnected");
        logMessage(`Conexión cerrada. Código: ${event.code}. Reintentando...`);
        startCentralMicBtn.disabled = true;
        stopCentralMicBtn.disabled = true;
        setTimeout(setupWebSocket, 5000);
    };

    socket.onerror = function(error) {
        console.error('Error de WebSocket:', error);
        updateStatus("Error de Conexión", "disconnected");
        logMessage(`Error de conexión`);
    };
}

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
