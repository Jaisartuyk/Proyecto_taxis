/**
 * REPRODUCTOR DE AUDIO GLOBAL
 * Este archivo se carga en TODAS las vistas de la app
 * Permite reproducir audio de walkie-talkie desde cualquier página
 */

console.log('🎵 Audio Player Global inicializado');

// Variable global para el audio actual
let globalCurrentAudio = null;
let globalAudioContext = null;

/**
 * Reproducir audio inmediatamente desde cualquier vista
 */
function playGlobalAudio(audioUrl, senderName = 'Central', volume = 1.0) {
    try {
        console.log(`🔊 [GLOBAL] Reproduciendo audio de: ${senderName}`);
        console.log(`📍 [GLOBAL] URL del audio: ${audioUrl.substring(0, 100)}...`);
        
        // Detener audio anterior si existe
        if (globalCurrentAudio) {
            globalCurrentAudio.pause();
            globalCurrentAudio = null;
        }
        
        // Crear nuevo elemento de audio
        const audioElement = new Audio();
        audioElement.src = audioUrl;
        audioElement.volume = volume;
        audioElement.preload = 'auto';
        
        globalCurrentAudio = audioElement;
        
        // Configurar Media Session API para reproducción en segundo plano
        if ('mediaSession' in navigator) {
            navigator.mediaSession.metadata = new MediaMetadata({
                title: `Audio de ${senderName}`,
                artist: 'De Aquí Pa\'llá - Central de Taxis',
                album: 'Comunicación Walkie-Talkie',
                artwork: [
                    { src: '/static/imagenes/icon-192x192.png', sizes: '192x192', type: 'image/png' },
                    { src: '/static/imagenes/icon-512x512.png', sizes: '512x512', type: 'image/png' }
                ]
            });
            
            navigator.mediaSession.setActionHandler('play', () => {
                audioElement.play();
            });
            
            navigator.mediaSession.setActionHandler('pause', () => {
                audioElement.pause();
            });
            
            navigator.mediaSession.setActionHandler('stop', () => {
                audioElement.pause();
                audioElement.currentTime = 0;
                globalCurrentAudio = null;
            });
            
            console.log('✅ [GLOBAL] Media Session configurada');
        }
        
        // Intentar reproducir
        const playPromise = audioElement.play();
        
        if (playPromise !== undefined) {
            playPromise.then(() => {
                console.log('✅ [GLOBAL] Audio reproduciéndose correctamente');
                
                // Mostrar notificación visual si estamos en la app
                showGlobalAudioNotification(senderName);
                
            }).catch(error => {
                console.error('❌ [GLOBAL] Error al reproducir audio:', error);
                
                // Si falla, mostrar alerta al usuario
                if (error.name === 'NotAllowedError') {
                    console.warn('⚠️ [GLOBAL] Autoplay bloqueado - Se requiere interacción del usuario');
                    showAutoplayBlockedWarning(senderName);
                }
            });
        }
        
        // Limpiar cuando termine
        audioElement.addEventListener('ended', () => {
            console.log('✅ [GLOBAL] Audio terminado');
            globalCurrentAudio = null;
            hideGlobalAudioNotification();
            
            // Limpiar Media Session
            if ('mediaSession' in navigator) {
                navigator.mediaSession.metadata = null;
            }
        });
        
        // Manejar errores
        audioElement.addEventListener('error', (e) => {
            console.error('❌ [GLOBAL] Error en el audio:', e);
            globalCurrentAudio = null;
            hideGlobalAudioNotification();
        });
        
    } catch (error) {
        console.error('❌ [GLOBAL] Error general al reproducir audio:', error);
    }
}

/**
 * Mostrar notificación visual de audio reproduciéndose
 */
function showGlobalAudioNotification(senderName) {
    // Crear o actualizar notificación
    let notification = document.getElementById('global-audio-notification');
    
    if (!notification) {
        notification = document.createElement('div');
        notification.id = 'global-audio-notification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            z-index: 10000;
            font-family: Arial, sans-serif;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideInRight 0.3s ease-out;
        `;
        document.body.appendChild(notification);
    }
    
    notification.innerHTML = `
        <span style="font-size: 20px;">🔊</span>
        <div>
            <div style="font-weight: bold;">Audio de ${senderName}</div>
            <div style="font-size: 12px; opacity: 0.9;">Reproduciéndose...</div>
        </div>
    `;
    
    notification.style.display = 'flex';
}

/**
 * Ocultar notificación visual
 */
function hideGlobalAudioNotification() {
    const notification = document.getElementById('global-audio-notification');
    if (notification) {
        notification.style.display = 'none';
    }
}

/**
 * Mostrar advertencia de autoplay bloqueado
 */
function showAutoplayBlockedWarning(senderName) {
    const warning = document.createElement('div');
    warning.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        color: #333;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        z-index: 10001;
        text-align: center;
        max-width: 90%;
        width: 400px;
    `;
    
    warning.innerHTML = `
        <div style="font-size: 50px; margin-bottom: 15px;">🔊</div>
        <h3 style="margin: 0 0 10px 0; color: #667eea;">Audio de ${senderName}</h3>
        <p style="margin: 0 0 20px 0; color: #666;">
            Toca el botón para escuchar el audio
        </p>
        <button id="play-blocked-audio" style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        ">
            🔊 Reproducir Audio
        </button>
    `;
    
    document.body.appendChild(warning);
    
    // Manejar click en el botón
    document.getElementById('play-blocked-audio').addEventListener('click', () => {
        if (globalCurrentAudio) {
            globalCurrentAudio.play();
        }
        document.body.removeChild(warning);
    });
    
    // Cerrar al hacer click fuera
    setTimeout(() => {
        warning.addEventListener('click', (e) => {
            if (e.target === warning) {
                document.body.removeChild(warning);
            }
        });
    }, 100);
}

/**
 * Inicializar contexto de audio
 */
function initGlobalAudioContext() {
    if (!globalAudioContext && ('AudioContext' in window || 'webkitAudioContext' in window)) {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        globalAudioContext = new AudioContextClass();
        
        if (globalAudioContext.state === 'suspended') {
            globalAudioContext.resume().then(() => {
                console.log('✅ [GLOBAL] Contexto de audio activado');
            });
        }
    }
}

// Inicializar al cargar
document.addEventListener('DOMContentLoaded', () => {
    initGlobalAudioContext();
    console.log('✅ [GLOBAL] Audio Player listo');
});

// Escuchar mensajes del Service Worker
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('message', (event) => {
        console.log('📨 [GLOBAL] Mensaje del Service Worker:', event.data);
        
        if (event.data && event.data.type === 'PLAY_AUDIO_IMMEDIATELY') {
            const { audioUrl, senderName, background } = event.data;
            
            console.log(`🔊 [GLOBAL] Reproducción solicitada: ${senderName}`);
            
            // Reproducir audio
            playGlobalAudio(audioUrl, senderName, 1.0);
        }
    });
    
    console.log('✅ [GLOBAL] Listener del Service Worker configurado');
}

// Agregar animación CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);

console.log('🎵 [GLOBAL] Sistema de audio global completamente inicializado');
