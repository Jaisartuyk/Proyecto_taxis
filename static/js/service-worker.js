/**
 * Service Worker v5.4 - LIMPIEZA DE CACHE - Con soporte para Push Notifications
 * De Aquí Pa'llá - Sistema de Taxis
 * Actualizado: 2025-12-11 - Forzar actualización de cache
 */

const CACHE_VERSION = 'v5.4';
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
                return cache.addAll(urlsToCache);
            })
            .then(() => {
                console.log('✅ Service Worker instalado');
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
    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Clonar la respuesta
                const responseToCache = response.clone();
                
                // Guardar en cache
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, responseToCache);
                });
                
                return response;
            })
            .catch(() => {
                // Si falla la red, buscar en cache
                return caches.match(event.request).then((response) => {
                    if (response) {
                        return response;
                    }
                    
                    // Si no está en cache y es navegación, retornar respuesta genérica
                    if (event.request.mode === 'navigate') {
                        return new Response(
                            '<html><head><title>Sin conexión</title></head><body><h1>Sin conexión a Internet</h1><p>Por favor, verifica tu conexión e intenta nuevamente.</p></body></html>',
                            { headers: { 'Content-Type': 'text/html' } }
                        );
                    }
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
    
    event.notification.close();

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

console.log('✅ Service Worker v5.4 cargado con soporte Push Notifications completo');
