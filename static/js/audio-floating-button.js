/**
 * Botón Flotante Global para Audio
 * Permite escuchar y responder audios desde cualquier vista
 */

// Variables globales
let globalAudioSocket = null;
let globalAudioQueue = [];
let isPlayingGlobalAudio = false;
let globalCurrentAudio = null;
let globalMediaRecorder = null;
let globalAudioStream = null;
let isRecording = false;
let currentUserId = null;

// Estado del botón flotante
let floatingButtonVisible = false;
let audioPanelExpanded = false;

/**
 * Inicializar el botón flotante de audio
 */
function initFloatingAudioButton() {
    console.log('[FLOATING AUDIO] Inicializando botón flotante...');
    
    // No inicializar en la vista de comunicación central (ya tiene su propio sistema)
    if (window.location.pathname === '/central-comunicacion/' || 
        document.body.classList.contains('central-comunicacion-page')) {
        console.log('[FLOATING AUDIO] En vista de comunicación central, no se inicializa');
        return;
    }
    
    // Obtener ID del usuario actual
    const userDataElement = document.querySelector('[data-user-id]');
    if (userDataElement) {
        currentUserId = userDataElement.getAttribute('data-user-id');
    }
    
    // Verificar si el usuario está autenticado
    const authElement = document.querySelector('[data-user-authenticated]');
    if (!authElement || authElement.getAttribute('data-user-authenticated') !== 'true') {
        console.log('[FLOATING AUDIO] Usuario no autenticado, no se inicializa');
        return;
    }
    
    // Crear el HTML del botón flotante si no existe
    if (!document.getElementById('floating-audio-container')) {
        createFloatingButtonHTML();
    }
    
    // Conectar WebSocket de audio
    connectGlobalAudioWebSocket();
    
    // Configurar eventos
    setupFloatingButtonEvents();
    
    // Mostrar el botón
    showFloatingButton();
    
    console.log('[FLOATING AUDIO] Botón flotante inicializado correctamente');
}

/**
 * Crear el HTML del botón flotante
 */
function createFloatingButtonHTML() {
    const container = document.createElement('div');
    container.id = 'floating-audio-container';
    container.innerHTML = `
        <!-- Botón flotante principal -->
        <button id="floating-audio-btn" class="floating-audio-btn" title="Audio Walkie-Talkie">
            <span id="floating-audio-icon">🎤</span>
            <span id="floating-audio-badge" class="floating-audio-badge" style="display: none;">0</span>
        </button>
        
        <!-- Panel de audio expandido -->
        <div id="floating-audio-panel" class="floating-audio-panel" style="display: none;">
            <div class="floating-audio-panel-header">
                <h5>🎤 Walkie-Talkie</h5>
                <button id="close-audio-panel" class="btn-close-audio">✕</button>
            </div>
            
            <div class="floating-audio-panel-body">
                <!-- Estado de conexión -->
                <div id="audio-connection-status" class="audio-status">
                    <span class="status-dot" id="audio-status-dot"></span>
                    <span id="audio-status-text">Conectando...</span>
                </div>
                
                <!-- Lista de audios pendientes -->
                <div id="audio-queue-list" class="audio-queue-list">
                    <p class="text-muted small">No hay audios pendientes</p>
                </div>
                
                <!-- Controles de audio -->
                <div class="audio-controls">
                    <button id="record-audio-btn-floating" class="btn-record-audio" 
                            onmousedown="startRecordingFloating()" 
                            onmouseup="stopRecordingFloating()" 
                            ontouchstart="startRecordingFloating()" 
                            ontouchend="stopRecordingFloating()">
                        🎤 Mantén presionado para hablar
                    </button>
                    <div id="recording-indicator" class="recording-indicator" style="display: none;">
                        <span class="recording-dot"></span>
                        <span>Grabando...</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Reproductor de audio oculto -->
        <audio id="floating-audio-player" style="display: none;"></audio>
    `;
    
    document.body.appendChild(container);
}

/**
 * Configurar eventos del botón flotante
 */
function setupFloatingButtonEvents() {
    const btn = document.getElementById('floating-audio-btn');
    const panel = document.getElementById('floating-audio-panel');
    const closeBtn = document.getElementById('close-audio-panel');
    
    if (btn) {
        btn.addEventListener('click', () => {
            toggleAudioPanel();
        });
    }
    
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            closeAudioPanel();
        });
    }
    
    // Cerrar panel al hacer clic fuera
    document.addEventListener('click', (e) => {
        if (panel && panel.style.display !== 'none') {
            if (!panel.contains(e.target) && !btn.contains(e.target)) {
                closeAudioPanel();
            }
        }
    });
}

/**
 * Mostrar/ocultar panel de audio
 */
function toggleAudioPanel() {
    const panel = document.getElementById('floating-audio-panel');
    if (!panel) return;
    
    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        audioPanelExpanded = true;
    } else {
        panel.style.display = 'none';
        audioPanelExpanded = false;
    }
}

/**
 * Cerrar panel de audio
 */
function closeAudioPanel() {
    const panel = document.getElementById('floating-audio-panel');
    if (panel) {
        panel.style.display = 'none';
        audioPanelExpanded = false;
    }
}

/**
 * Mostrar botón flotante
 */
function showFloatingButton() {
    const container = document.getElementById('floating-audio-container');
    if (container) {
        container.style.display = 'block';
        floatingButtonVisible = true;
    }
}

/**
 * Ocultar botón flotante
 */
function hideFloatingButton() {
    const container = document.getElementById('floating-audio-container');
    if (container) {
        container.style.display = 'none';
        floatingButtonVisible = false;
    }
}

/**
 * Conectar WebSocket de audio global
 */
function connectGlobalAudioWebSocket() {
    // Solo conectar si no estamos en la vista de comunicación (para evitar duplicados)
    if (window.location.pathname === '/central-comunicacion/' || 
        document.body.classList.contains('central-comunicacion-page')) {
        console.log('[FLOATING AUDIO] En vista de comunicación, usando WebSocket existente');
        return;
    }
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/audio/conductores/`;
    
    console.log('[FLOATING AUDIO] Conectando WebSocket:', wsUrl);
    
    globalAudioSocket = new WebSocket(wsUrl);
    
    globalAudioSocket.onopen = () => {
        console.log('[FLOATING AUDIO] WebSocket conectado');
        updateConnectionStatus(true);
    };
    
    globalAudioSocket.onclose = () => {
        console.log('[FLOATING AUDIO] WebSocket desconectado');
        updateConnectionStatus(false);
        // Reconectar después de 3 segundos
        setTimeout(connectGlobalAudioWebSocket, 3000);
    };
    
    globalAudioSocket.onerror = (error) => {
        console.error('[FLOATING AUDIO] Error en WebSocket:', error);
        updateConnectionStatus(false);
    };
    
    globalAudioSocket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleGlobalAudioMessage(data);
        } catch (error) {
            console.error('[FLOATING AUDIO] Error parseando mensaje:', error);
        }
    };
}

/**
 * Manejar mensajes de audio recibidos
 */
function handleGlobalAudioMessage(data) {
    console.log('[FLOATING AUDIO] Mensaje recibido:', data.type);
    
    if (data.type === 'audio_message' || data.type === 'central_audio' || data.type === 'audio_broadcast') {
        const audioData = data.audio_data || data.audio;
        const senderId = data.senderId || data.sender_id || data.driver_id;
        const senderName = data.senderName || data.sender_name || 'Desconocido';
        
        // Ignorar audio propio
        if (senderId && currentUserId && String(senderId) === String(currentUserId)) {
            console.log('[FLOATING AUDIO] Audio propio ignorado');
            return;
        }
        
        if (audioData) {
            // Agregar a la cola
            globalAudioQueue.push({
                audioData: audioData,
                senderName: senderName,
                senderId: senderId,
                timestamp: Date.now()
            });
            
            // Actualizar badge
            updateAudioBadge(globalAudioQueue.length);
            
            // Actualizar lista de audios
            updateAudioQueueList();
            
            // Reproducir si no hay audio en reproducción
            if (!isPlayingGlobalAudio) {
                playNextGlobalAudio();
            }
        }
    }
}

/**
 * Reproducir siguiente audio de la cola
 */
function playNextGlobalAudio() {
    if (globalAudioQueue.length === 0) {
        isPlayingGlobalAudio = false;
        updateAudioBadge(0);
        return;
    }
    
    isPlayingGlobalAudio = true;
    const audioItem = globalAudioQueue.shift();
    
    // Convertir base64 a Blob
    const audioBlob = base64ToBlob(audioItem.audioData, 'audio/webm');
    const audioUrl = URL.createObjectURL(audioBlob);
    
    const audioPlayer = document.getElementById('floating-audio-player');
    if (!audioPlayer) {
        console.error('[FLOATING AUDIO] Reproductor no encontrado');
        isPlayingGlobalAudio = false;
        playNextGlobalAudio();
        return;
    }
    
    audioPlayer.src = audioUrl;
    audioPlayer.volume = 1.0;
    
    // Configurar Media Session
    if ('mediaSession' in navigator) {
        navigator.mediaSession.metadata = new MediaMetadata({
            title: `Audio de ${audioItem.senderName}`,
            artist: 'De Aquí Pa\'llá - Central de Taxis',
            artwork: [
                { src: '/static/imagenes/icon-192x192.png', sizes: '192x192', type: 'image/png' }
            ]
        });
    }
    
    audioPlayer.play()
        .then(() => {
            console.log('[FLOATING AUDIO] Reproduciendo audio de:', audioItem.senderName);
            updateAudioBadge(globalAudioQueue.length);
            updateAudioQueueList();
        })
        .catch(error => {
            console.error('[FLOATING AUDIO] Error reproduciendo audio:', error);
            isPlayingGlobalAudio = false;
            playNextGlobalAudio();
        });
    
    audioPlayer.onended = () => {
        URL.revokeObjectURL(audioUrl);
        isPlayingGlobalAudio = false;
        playNextGlobalAudio();
    };
}

/**
 * Convertir base64 a Blob
 */
function base64ToBlob(base64, mimeType) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
}

/**
 * Actualizar badge de audios pendientes
 */
function updateAudioBadge(count) {
    const badge = document.getElementById('floating-audio-badge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    }
}

/**
 * Actualizar lista de audios en cola
 */
function updateAudioQueueList() {
    const list = document.getElementById('audio-queue-list');
    if (!list) return;
    
    if (globalAudioQueue.length === 0) {
        list.innerHTML = '<p class="text-muted small">No hay audios pendientes</p>';
    } else {
        list.innerHTML = globalAudioQueue.map((item, index) => `
            <div class="audio-queue-item">
                <span class="audio-sender">${item.senderName}</span>
                <span class="audio-time">${new Date(item.timestamp).toLocaleTimeString()}</span>
            </div>
        `).join('');
    }
}

/**
 * Actualizar estado de conexión
 */
function updateConnectionStatus(connected) {
    const statusDot = document.getElementById('audio-status-dot');
    const statusText = document.getElementById('audio-status-text');
    
    if (statusDot) {
        statusDot.className = connected ? 'status-dot status-connected' : 'status-dot status-disconnected';
    }
    
    if (statusText) {
        statusText.textContent = connected ? 'Conectado' : 'Desconectado';
    }
}

/**
 * Iniciar grabación de audio
 */
async function startRecordingFloating() {
    if (isRecording) return;
    
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        globalAudioStream = stream;
        globalMediaRecorder = new MediaRecorder(stream);
        const audioChunks = [];
        
        globalMediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        globalMediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            await sendFloatingAudio(audioBlob);
            
            // Detener stream
            if (globalAudioStream) {
                globalAudioStream.getTracks().forEach(track => track.stop());
                globalAudioStream = null;
            }
        };
        
        globalMediaRecorder.start();
        isRecording = true;
        
        // Mostrar indicador de grabación
        const indicator = document.getElementById('recording-indicator');
        if (indicator) indicator.style.display = 'block';
        
        console.log('[FLOATING AUDIO] Grabación iniciada');
    } catch (error) {
        console.error('[FLOATING AUDIO] Error iniciando grabación:', error);
        alert('Error al acceder al micrófono. Por favor, permite el acceso al micrófono.');
    }
}

/**
 * Detener grabación de audio
 */
function stopRecordingFloating() {
    if (!isRecording || !globalMediaRecorder) return;
    
    globalMediaRecorder.stop();
    isRecording = false;
    
    // Ocultar indicador de grabación
    const indicator = document.getElementById('recording-indicator');
    if (indicator) indicator.style.display = 'none';
    
    console.log('[FLOATING AUDIO] Grabación detenida');
}

/**
 * Enviar audio grabado
 */
async function sendFloatingAudio(audioBlob) {
    if (!globalAudioSocket || globalAudioSocket.readyState !== WebSocket.OPEN) {
        console.error('[FLOATING AUDIO] WebSocket no conectado');
        alert('No hay conexión. Por favor, espera a que se reconecte.');
        return;
    }
    
    try {
        const reader = new FileReader();
        reader.onloadend = () => {
            const base64Audio = reader.result.split(',')[1];
            
            const message = {
                type: 'central_audio',
                audio_data: base64Audio,
                senderId: currentUserId,
                senderRole: 'Central'
            };
            
            globalAudioSocket.send(JSON.stringify(message));
            console.log('[FLOATING AUDIO] Audio enviado');
        };
        
        reader.readAsDataURL(audioBlob);
    } catch (error) {
        console.error('[FLOATING AUDIO] Error enviando audio:', error);
    }
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFloatingAudioButton);
} else {
    initFloatingAudioButton();
}

