/**
 * Service Worker v5.4 - LIMPIEZA DE CACHE - Con soporte para Push Notifications
 * De Aquí Pa'llá - Sistema de Taxis
 * Actualizado: 2025-12-11 - Forzar actualización de cache
 */

const CACHE_VERSION = 'v5.5';
const CACHE_NAME = `deaquipalla-${CACHE_VERSION}`;

// Archivos para cachear (solo archivos que existen)
const urlsToCache = [
    '/',
    '/static/css/theme.css',
    '/static/js/app.js',
    '/static/js/badge-manager.js',
    '/static/js/chat-badge.js',
    '/static/js/notifications-v5.js',
    '/static/manifest.json',
    '/static/imagenes/DE_AQU_PALL_Logo.png',
    '/static/imagenes/logo1.png',
    '/static/imagenes/icon-192x192.png',
    '/static/imagenes/icon-512x512.png'
];

// Instalación del Service Worker
self.addEventListener('install', (event) => {
    console.log('🔧 Service Worker: Instalando...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('📦 Cache abierto');
                // Usar Promise.allSettled para manejar errores individuales
                // Esto evita que un archivo faltante rompa toda la instalación
                return Promise.allSettled(
                    urlsToCache.map(url => {
                        return cache.add(url).catch(err => {
                            console.warn(`⚠️ No se pudo cachear ${url}:`, err);
                            return null; // Continuar aunque falle
                        });
                    })
                );
            })
            .then(() => {
                console.log('✅ Service Worker instalado');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('❌ Error instalando Service Worker:', error);
                // Continuar aunque haya errores
                return self.skipWaiting();
            })
    );
});

// Activación del Service Worker
self.addEventListener('activate', (event) => {
    console.log('🚀 Service Worker: Activando...');

    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('🗑️ Eliminando cache antigua:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('✅ Service Worker activado');
            return self.clients.claim();
        })
    );
});

// Estrategia de caché: Network First, fallback a Cache
self.addEventListener('fetch', (event) => {
    // Ignorar requests que no sean GET (POST, PUT, DELETE, etc.)
    if (event.request.method !== 'GET') {
        return;
    }

    // Ignorar requests a APIs externas o WebSockets
    const url = new URL(event.request.url);
    if (url.protocol === 'ws:' || url.protocol === 'wss:' ||
        url.hostname !== self.location.hostname) {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Solo cachear respuestas exitosas
                if (!response || response.status !== 200 || response.type === 'error') {
                    return response;
                }

                // Clonar la respuesta
                const responseToCache = response.clone();

                // Guardar en cache solo si es exitoso
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, responseToCache);
                }).catch(err => {
                    console.warn('⚠️ No se pudo cachear:', event.request.url, err);
                });

                return response;
            })
            .catch((error) => {
                console.warn('⚠️ Fetch falló para:', event.request.url, error);

                // Si falla la red, buscar en cache
                return caches.match(event.request).then((response) => {
                    if (response) {
                        console.log('✅ Sirviendo desde cache:', event.request.url);
                        return response;
                    }

                    // Si no está en cache y es navegación, retornar respuesta genérica
                    if (event.request.mode === 'navigate') {
                        return new Response(
                            '<html><head><title>Sin conexión</title></head><body><h1>Sin conexión a Internet</h1><p>Por favor, verifica tu conexión e intenta nuevamente.</p></body></html>',
                            { headers: { 'Content-Type': 'text/html' } }
                        );
                    }

                    // Para otros recursos, retornar error
                    return new Response('Recurso no disponible', {
                        status: 503,
                        statusText: 'Service Unavailable'
                    });
                });
            })
    );
});

// ============================================
// NOTIFICACIONES PUSH
// ============================================

/**
 * Evento: Push recibido
 * Se ejecuta cuando llega una notificación push del servidor
 */
self.addEventListener('push', (event) => {
    console.log('📬 Push recibido:', event);

    let notificationData = {
        title: '🚕 Nueva carrera disponible',
        body: 'Hay una nueva carrera cerca de ti',
        icon: '/static/imagenes/DE_AQU_PALL_Logo.png',
        badge: '/static/imagenes/logo1.png',
        vibrate: [200, 100, 200, 100, 200],
        tag: 'nueva-carrera',
        requireInteraction: true,
        data: {
            url: '/available-rides/',
            timestamp: Date.now()
        },
        actions: [
            {
                action: 'ver',
                title: '👀 Ver carrera',
                icon: '/static/imagenes/logo1.png'
            },
            {
                action: 'cerrar',
                title: '✖️ Cerrar'
            }
        ]
    };

    // Si el push trae datos, usarlos
    if (event.data) {
        try {
            const pushData = event.data.json();
            console.log('📦 Datos del push:', pushData);

            // Actualizar con datos del servidor
            if (pushData.title) notificationData.title = pushData.title;
            if (pushData.body) notificationData.body = pushData.body;
            if (pushData.icon) notificationData.icon = pushData.icon;
            if (pushData.badge) notificationData.badge = pushData.badge;
            if (pushData.data) notificationData.data = { ...notificationData.data, ...pushData.data };

            // CONFIGURACIÓN ESPECIAL PARA AUDIO WALKIE-TALKIE
            if (pushData.data && pushData.data.type === 'walkie_talkie_audio') {
                console.log('📻 AUDIO WALKIE-TALKIE RECIBIDO - REPRODUCIENDO AUTOMÁTICAMENTE');
                console.log('🎵 Datos del audio:', {
                    sender: pushData.data.sender_name,
                    urgent: pushData.data.urgent,
                    audioLength: pushData.data.audio_url ? pushData.data.audio_url.length : 'No audio'
                });

                const audioUrl = pushData.data.audio_url;
                const senderName = pushData.data.sender_name;

                if (audioUrl && senderName) {
                    // ESTRATEGIA INTELIGENTE PARA REPRODUCCIÓN AUTOMÁTICA
                    event.waitUntil(
                        self.clients.matchAll({
                            type: 'window',
                            includeUncontrolled: true
                        }).then(clients => {
                            console.log(`🔍 Clientes encontrados: ${clients.length}`);

                            if (clients.length > 0) {
                                // ✅ HAY VENTANA ABIERTA - Reproducir en segundo plano
                                const client = clients[0];
                                console.log('📱 App abierta - Reproduciendo audio en segundo plano');

                                // Enviar mensaje al cliente para reproducir audio
                                client.postMessage({
                                    type: 'PLAY_AUDIO_IMMEDIATELY',
                                    audioUrl: audioUrl,
                                    senderName: senderName,
                                    timestamp: Date.now(),
                                    background: true // No enfocar la ventana
                                });

                                console.log('🔇 Audio reproduciéndose sin interrumpir al usuario');

                                // Retornar promesa resuelta
                                return Promise.resolve();
                            } else {
                                // ❌ NO HAY VENTANA - Abrir app automáticamente
                                console.log('🆕 App cerrada - Abriendo automáticamente para reproducir');

                                // Abrir la app en comunicación con parámetros de autoplay
                                return self.clients.openWindow(
                                    '/central-comunicacion/?autoplay=true&audio=' +
                                    encodeURIComponent(audioUrl) +
                                    '&sender=' + encodeURIComponent(senderName) +
                                    '&background=true' // Indicar que debe reproducir automáticamente
                                ).then(windowClient => {
                                    console.log('✅ App abierta automáticamente');

                                    // Esperar a que la ventana cargue y enviar el audio
                                    if (windowClient) {
                                        setTimeout(() => {
                                            windowClient.postMessage({
                                                type: 'PLAY_AUDIO_IMMEDIATELY',
                                                audioUrl: audioUrl,
                                                senderName: senderName,
                                                timestamp: Date.now(),
                                                background: true
                                            });
                                        }, 1000); // Esperar 1 segundo para que cargue
                                    }

                                    return windowClient;
                                });
                            }
                        })
                    );

                    console.log('🔊 COMANDO DE REPRODUCCIÓN ENVIADO');
                } else {
                    console.error('❌ Datos de audio incompletos:', {
                        audioUrl: !!audioUrl,
                        senderName: !!senderName
                    });
                }

                // NOTIFICACIÓN SILENCIOSA - Solo para informar, no molestar
                notificationData.silent = true; // SILENCIOSO - no hace sonido
                notificationData.tag = 'walkie-talkie-audio'; // Agrupar audios (reemplaza la anterior)
                notificationData.renotify = false; // NO volver a notificar
                notificationData.requireInteraction = false; // Se cierra automáticamente

                // Vibración suave solo para indicar que llegó algo
                notificationData.vibrate = [100]; // Una sola vibración corta

                // Cambiar el título para que sea menos intrusivo
                notificationData.title = `🎙️ ${senderName}`;
                notificationData.body = 'Audio reproduciéndose...';

                // Acciones rápidas
                notificationData.actions = [
                    {
                        action: 'open_and_play',
                        title: '📱 Abrir App',
                        icon: '/static/imagenes/icon-192x192.png'
                    }
                ];

                // Guardar audio pendiente para cuando abra la app
                savePendingAudio(
                    pushData.data.sender_id,
                    pushData.data.sender_name,
                    pushData.data.audio_url,
                    pushData.data.timestamp || Date.now()
                );
            }

        } catch (e) {
            console.error('❌ Error al parsear datos del push:', e);
        }
    }

    // Actualizar el badge del ícono de la app
    const updateBadge = async () => {
        if ('setAppBadge' in navigator) {
            try {
                // Obtener el conteo actual
                const response = await fetch('/api/badge-count/');
                if (response.ok) {
                    const data = await response.json();
                    await navigator.setAppBadge(data.count);
                    console.log(`📛 Badge actualizado: ${data.count}`);
                }
            } catch (error) {
                console.error('Error al actualizar badge:', error);
            }
        }
    };

    event.waitUntil(
        Promise.all([
            self.registration.showNotification(notificationData.title, notificationData)
                .then(() => console.log('✅ Notificación mostrada'))
                .catch(err => console.error('❌ Error al mostrar notificación:', err)),
            updateBadge()
        ])
    );
});

/**
 * Evento: Click en notificación
 * Se ejecuta cuando el usuario hace click en la notificación
 */
self.addEventListener('notificationclick', (event) => {
    console.log('🖱️ Click en notificación:', event.action);

    const notificationData = event.notification.data || {};
    const action = event.action;

    event.notification.close();

    // MANEJO ESPECÍFICO PARA AUDIO WALKIE-TALKIE
    if (notificationData.type === 'walkie_talkie_audio' || notificationData.type === 'background_audio_playback') {
        console.log('📻 Click en notificación de walkie-talkie');

        if (action === 'open_and_play' || action === 'replay_audio' || !action) {
            console.log('🔊 Abriendo app para reproducir audio');

            // Abrir app y enviar comando para reproducir audio
            event.waitUntil(
                clients.matchAll({
                    type: 'window',
                    includeUncontrolled: true
                }).then((clientList) => {
                    console.log(`🔍 Ventanas encontradas: ${clientList.length}`);

                    // Si hay una ventana abierta, navegar a comunicación
                    if (clientList.length > 0) {
                        const client = clientList[0];
                        console.log('📱 Navegando a comunicación y enviando audio');

                        // Navegar a la vista de comunicación
                        client.navigate('/central-comunicacion/').then(() => {
                            // Esperar un momento para que cargue la página
                            setTimeout(() => {
                                // Enviar mensaje al cliente para reproducir audio
                                client.postMessage({
                                    type: 'PLAY_AUDIO_IMMEDIATELY',
                                    audioUrl: notificationData.audio_url,
                                    senderName: notificationData.sender_name,
                                    timestamp: Date.now()
                                });
                            }, 500);
                        }).catch(err => {
                            console.error('Error al navegar:', err);
                            // Si falla la navegación, solo enfocar y enviar audio
                            client.postMessage({
                                type: 'PLAY_AUDIO_IMMEDIATELY',
                                audioUrl: notificationData.audio_url,
                                senderName: notificationData.sender_name,
                                timestamp: Date.now()
                            });
                        });

                        return client.focus();
                    } else {
                        // Si no hay ventana abierta, abrir directamente en comunicación
                        console.log('🆕 Abriendo comunicación directamente');
                        if (clients.openWindow) {
                            return clients.openWindow('/central-comunicacion/?autoplay=true&audio=' + encodeURIComponent(notificationData.audio_url) + '&sender=' + encodeURIComponent(notificationData.sender_name));
                        }
                    }
                })
            );
        } else if (action === 'dismiss') {
            console.log('📻 Audio walkie-talkie descartado');
            // Marcar como descartado en localStorage
            if (notificationData.sender_id && notificationData.timestamp) {
                markAudioAsDismissed(notificationData.sender_id, notificationData.timestamp);
            }
        }
    } else {
        // Comportamiento normal para otras notificaciones
        event.waitUntil(
            clients.matchAll({ type: 'window' }).then((clientList) => {
                for (const client of clientList) {
                    if ('focus' in client) {
                        return client.focus();
                    }
                }
                if (clients.openWindow) {
                    return clients.openWindow('/');
                }
            })
        );
    }

    // Actualizar badge al hacer clic
    const updateBadge = async () => {
        if ('setAppBadge' in navigator) {
            try {
                const response = await fetch('/api/badge-count/');
                if (response.ok) {
                    const data = await response.json();
                    await navigator.setAppBadge(data.count);
                    console.log(`📛 Badge actualizado después de clic: ${data.count}`);
                }
            } catch (error) {
                console.error('Error al actualizar badge:', error);
            }
        }
    };

    if (event.action === 'cerrar') {
        updateBadge();
        return;
    }

    // Acción por defecto o "ver"
    const urlToOpen = event.notification.data?.url || '/available-rides/';

    event.waitUntil(
        Promise.all([
            clients.matchAll({
                type: 'window',
                includeUncontrolled: true
            }).then((clientList) => {
                // Buscar si ya hay una ventana abierta
                for (const client of clientList) {
                    if (client.url.includes(urlToOpen) && 'focus' in client) {
                        return client.focus();
                    }
                }

                // Si no hay ventana abierta, abrir una nueva
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            }),
            updateBadge()
        ])
    );
});

/**
 * Evento: Cierre de notificación
 */
self.addEventListener('notificationclose', (event) => {
    console.log('🔕 Notificación cerrada:', event.notification.tag);
});

/**
 * Sincronización en segundo plano
 * Para verificar nuevas carreras periódicamente
 */
self.addEventListener('sync', (event) => {
    console.log('🔄 Sync event:', event.tag);

    if (event.tag === 'check-new-rides') {
        event.waitUntil(checkNewRides());
    }
});

/**
 * Verificar nuevas carreras
 */
async function checkNewRides() {
    try {
        const response = await fetch('/api/available-rides/');
        const data = await response.json();

        if (data.new_rides && data.new_rides.length > 0) {
            // Mostrar notificación
            await self.registration.showNotification('🚕 Nuevas carreras disponibles', {
                body: `Hay ${data.new_rides.length} carrera(s) nueva(s) cerca de ti`,
                icon: '/static/imagenes/icon-192x192.png',
                badge: '/static/imagenes/icon-72x72.png',
                vibrate: [200, 100, 200],
                tag: 'nuevas-carreras',
                data: {
                    url: '/available-rides/'
                }
            });
        }
    } catch (error) {
        console.error('Error al verificar nuevas carreras:', error);
    }
}

/**
 * Evento: Recibir notificación push
 */
self.addEventListener('push', (event) => {
    console.log('📨 Push recibido:', event);

    if (event.data) {
        const data = event.data.json();
        console.log('📄 Datos del push:', data);

        const notificationTitle = data.title || '🚕 De Aquí Pa\'llá';
        const notificationOptions = {
            body: data.body || 'Tienes una nueva notificación',
            icon: '/static/imagenes/icon-192x192.png',
            badge: '/static/imagenes/icon-72x72.png',
            vibrate: [200, 100, 200],
            tag: data.tag || 'general',
            data: {
                url: data.url || '/',
                timestamp: Date.now()
            },
            actions: [
                {
                    action: 'ver',
                    title: 'Ver',
                    icon: '/static/imagenes/icon-72x72.png'
                },
                {
                    action: 'cerrar',
                    title: 'Cerrar'
                }
            ],
            requireInteraction: true,
            silent: false
        };

        // Notificar a todas las ventanas/tabs abiertas
        event.waitUntil(
            Promise.all([
                // Mostrar la notificación del navegador
                self.registration.showNotification(notificationTitle, notificationOptions),

                // Enviar mensaje a las páginas abiertas para mostrar indicador visual
                self.clients.matchAll({ includeUncontrolled: true, type: 'window' }).then(clients => {
                    clients.forEach(client => {
                        client.postMessage({
                            type: 'PUSH_RECEIVED',
                            title: notificationTitle,
                            body: notificationOptions.body,
                            data: data
                        });
                    });
                })
            ])
        );
    } else {
        console.log('📭 Push sin datos recibido');
        event.waitUntil(
            self.registration.showNotification('🚕 De Aquí Pa\'llá', {
                body: 'Nueva notificación disponible',
                icon: '/static/imagenes/icon-192x192.png',
                tag: 'default'
            })
        );
    }
});

// ========================================
// FUNCIONES DE GESTIÓN DE AUDIO WALKIE-TALKIE
// ========================================

/**
 * Reproduce audio inmediatamente en background sin requerir interacción del usuario
 */
async function playAudioInBackground(audioUrl, senderName) {
    try {
        console.log(`🔊 REPRODUCIENDO AUDIO EN BACKGROUND de: ${senderName}`);
        console.log(`🎵 URL del audio: ${audioUrl.substring(0, 100)}...`);

        // Método 1: Usar Audio API directamente en Service Worker
        try {
            const audio = new Audio();
            audio.src = audioUrl;
            audio.volume = 1.0; // Volumen máximo
            audio.preload = 'auto';

            // FORZAR REPRODUCCIÓN INMEDIATA
            console.log(`🎵 Iniciando reproducción inmediata...`);
            const playPromise = audio.play();

            if (playPromise !== undefined) {
                playPromise
                    .then(() => {
                        console.log(`✅ AUDIO REPRODUCIÉNDOSE EN BACKGROUND: ${senderName}`);

                        // Mostrar notificación de confirmación
                        self.registration.showNotification(`🔊 Reproduciendo: ${senderName}`, {
                            body: '🎵 Audio de walkie-talkie en curso...',
                            icon: '/static/imagenes/icon-192x192.png',
                            tag: 'audio-playing',
                            requireInteraction: false,
                            silent: true, // No sonido adicional, solo el audio
                            vibrate: [100],
                            data: { type: 'audio_playing_notification' }
                        });

                        // Auto-cerrar notificación de reproducción después de 3 segundos
                        setTimeout(() => {
                            self.registration.getNotifications({ tag: 'audio-playing' })
                                .then(notifications => {
                                    notifications.forEach(notification => notification.close());
                                });
                        }, 3000);
                    })
                    .catch(error => {
                        console.error(`❌ Error reproduciendo con Audio API:`, error);
                        console.log(`🔄 Intentando método de fallback...`);
                        fallbackAudioPlayback(audioUrl, senderName);
                    });
            }

            // Configurar eventos del audio
            audio.addEventListener('ended', () => {
                console.log(`🏁 Audio de ${senderName} terminó de reproducirse`);
            });

            audio.addEventListener('error', (error) => {
                console.error(`❌ Error cargando audio:`, error);
                fallbackAudioPlayback(audioUrl, senderName);
            });

        } catch (audioError) {
            console.error(`❌ Error creando objeto Audio:`, audioError);
            fallbackAudioPlayback(audioUrl, senderName);
        }

    } catch (error) {
        console.error('❌ Error en playAudioInBackground:', error);
        fallbackAudioPlayback(audioUrl, senderName);
    }
}

/**
 * Método alternativo para reproducir audio cuando el principal falla
 */
async function fallbackAudioPlayback(audioUrl, senderName) {
    try {
        console.log(`🔄 FALLBACK: Reproducción de audio de ${senderName}`);

        // Método 2: Crear notificación con sonido más intenso
        await createAudioNotification(audioUrl, senderName);

        // Método 3: Enviar comando a todas las ventanas/tabs abiertas
        const clients = await self.clients.matchAll({
            type: 'window',
            includeUncontrolled: true
        });

        if (clients.length > 0) {
            console.log(`📢 Enviando comando de audio urgente a ${clients.length} ventana(s)`);

            // Enviar a TODAS las ventanas abiertas
            clients.forEach(client => {
                client.postMessage({
                    type: 'PLAY_AUDIO_IMMEDIATELY',
                    payload: {
                        audioUrl: audioUrl,
                        senderName: senderName,
                        urgent: true,
                        volume: 1.0,
                        background: true
                    }
                });
            });
        }

        // Método 4: Usar Web Audio API si está disponible
        try {
            await playWithWebAudioAPI(audioUrl, senderName);
        } catch (webAudioError) {
            console.warn(`⚠️ Web Audio API falló:`, webAudioError);
        }

    } catch (error) {
        console.error('❌ Error en fallbackAudioPlayback:', error);
    }
}

/**
 * Intentar reproducción con Web Audio API
 */
async function playWithWebAudioAPI(audioUrl, senderName) {
    try {
        console.log(`🎛️ Intentando Web Audio API para ${senderName}`);

        // Convertir base64 a ArrayBuffer
        if (audioUrl.startsWith('data:audio/')) {
            const base64Data = audioUrl.split(',')[1];
            const binaryData = atob(base64Data);
            const arrayBuffer = new ArrayBuffer(binaryData.length);
            const uint8Array = new Uint8Array(arrayBuffer);

            for (let i = 0; i < binaryData.length; i++) {
                uint8Array[i] = binaryData.charCodeAt(i);
            }

            // Crear contexto de audio
            const audioContext = new (AudioContext || webkitAudioContext)();

            // Decodificar y reproducir
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
            const source = audioContext.createBufferSource();
            const gainNode = audioContext.createGain();

            source.buffer = audioBuffer;
            gainNode.gain.value = 1.0; // Volumen máximo

            source.connect(gainNode);
            gainNode.connect(audioContext.destination);

            source.start(0);

            console.log(`✅ Web Audio API reproduciendo: ${senderName}`);

            source.addEventListener('ended', () => {
                console.log(`🏁 Web Audio terminó: ${senderName}`);
                audioContext.close();
            });

        }
    } catch (error) {
        console.warn(`⚠️ Web Audio API no pudo reproducir:`, error);
        throw error;
    }
}

/**
 * Crear notificación con sonido cuando no hay ventanas activas
 */
async function createAudioNotification(audioUrl, senderName) {
    try {
        console.log(`🔔 Creando notificación sonora para ${senderName}`);

        await self.registration.showNotification(`📻 AUDIO URGENTE: ${senderName}`, {
            body: '� MENSAJE DE WALKIE-TALKIE - Presiona para abrir y escuchar',
            icon: '/static/imagenes/icon-192x192.png',
            badge: '/static/imagenes/icon-72x72.png',
            tag: 'urgent-audio-background',
            requireInteraction: true, // MANTENER VISIBLE hasta que actúe
            silent: false, // SONIDO ACTIVADO
            vibrate: [500, 200, 500, 200, 500, 200, 500], // Vibración muy intensa
            actions: [
                {
                    action: 'open_and_play',
                    title: '🔊 ABRIR Y ESCUCHAR',
                    icon: '/static/imagenes/icon-72x72.png'
                },
                {
                    action: 'replay_audio',
                    title: '🔄 REPETIR AUDIO',
                    icon: '/static/imagenes/icon-72x72.png'
                }
            ],
            data: {
                type: 'urgent_background_audio',
                audioUrl: audioUrl,
                senderName: senderName,
                timestamp: Date.now(),
                urgent: true
            }
        });

        console.log(`✅ Notificación urgente creada para ${senderName}`);

        // Crear múltiples notificaciones para asegurar que se note
        setTimeout(async () => {
            try {
                await self.registration.showNotification(`🚨 AUDIO NO ESCUCHADO: ${senderName}`, {
                    body: '⚠️ Tienes un mensaje de audio pendiente',
                    icon: '/static/imagenes/icon-192x192.png',
                    tag: 'audio-reminder',
                    requireInteraction: true,
                    silent: false,
                    vibrate: [300, 100, 300],
                    data: {
                        type: 'audio_reminder',
                        audioUrl: audioUrl,
                        senderName: senderName
                    }
                });
            } catch (e) {
                console.warn('No se pudo crear notificación de recordatorio:', e);
            }
        }, 10000); // Recordatorio después de 10 segundos

    } catch (error) {
        console.error('❌ Error creando notificación de audio:', error);
    }
}

/**
 * Guarda un audio pendiente para reproducir cuando el usuario abra la app
 */
function savePendingAudio(senderId, senderName, audioUrl, timestamp) {
    return new Promise((resolve) => {
        try {
            // REPRODUCIR AUDIO INMEDIATAMENTE EN BACKGROUND
            playAudioInBackground(audioUrl, senderName);

            // Obtener lista actual de audios pendientes
            self.clients.matchAll({ type: 'window' }).then(clients => {
                if (clients.length > 0) {
                    // Usar postMessage si hay ventanas abiertas
                    clients[0].postMessage({
                        type: 'SAVE_PENDING_AUDIO',
                        payload: {
                            senderId: senderId,
                            senderName: senderName,
                            audioUrl: audioUrl,
                            timestamp: timestamp,
                            id: `audio_${senderId}_${timestamp}`
                        }
                    });
                }
            });

            console.log(`📻 Audio pendiente guardado: ${senderName} - ${timestamp}`);
            resolve();
        } catch (error) {
            console.error('❌ Error guardando audio pendiente:', error);
            resolve();
        }
    });
}

/**
 * Marca un audio como descartado para evitar reproducirlo
 */
function markAudioAsDismissed(senderId, timestamp) {
    return new Promise((resolve) => {
        try {
            self.clients.matchAll({ type: 'window' }).then(clients => {
                if (clients.length > 0) {
                    clients[0].postMessage({
                        type: 'DISMISS_AUDIO',
                        payload: {
                            senderId: senderId,
                            timestamp: timestamp,
                            id: `audio_${senderId}_${timestamp}`
                        }
                    });
                }
            });

            console.log(`📻 Audio marcado como descartado: ${senderId} - ${timestamp}`);
            resolve();
        } catch (error) {
            console.error('❌ Error marcando audio como descartado:', error);
            resolve();
        }
    });
}

/**
 * Limpia audios pendientes antiguos (más de 1 hora)
 */
function cleanOldPendingAudios() {
    return new Promise((resolve) => {
        try {
            const oneHourAgo = Date.now() - (60 * 60 * 1000);

            self.clients.matchAll({ type: 'window' }).then(clients => {
                if (clients.length > 0) {
                    clients[0].postMessage({
                        type: 'CLEAN_OLD_AUDIOS',
                        payload: {
                            beforeTimestamp: oneHourAgo
                        }
                    });
                }
            });

            console.log('🧹 Limpieza de audios antiguos solicitada');
            resolve();
        } catch (error) {
            console.error('❌ Error limpiando audios antiguos:', error);
            resolve();
        }
    });
}

// Limpiar audios antiguos cada 30 minutos
self.setInterval(() => {
    cleanOldPendingAudios();
}, 30 * 60 * 1000);

console.log('✅ Service Worker v5.4 cargado con soporte Push Notifications completo');
