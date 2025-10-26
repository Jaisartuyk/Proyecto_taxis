const CACHE_NAME = 'p-alla-cache-v1';
const URLS_TO_CACHE = [
    '/',
    '/static/css/theme.css',
    '/static/js/app.js',
    '/static/imagenes/logo1.png',
    '/offline.html'
];

// Evento de instalación: se dispara cuando el service worker se registra
self.addEventListener('install', event => {
    console.log('Service Worker: Instalando...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Service Worker: Cacheando archivos de la app shell');
                return cache.addAll(URLS_TO_CACHE);
            })
            .then(() => self.skipWaiting()) // Forzar la activación del nuevo SW
    );
});

// Evento de activación: se dispara después de la instalación
self.addEventListener('activate', event => {
    console.log('Service Worker: Activando...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cache => {
                    if (cache !== CACHE_NAME) {
                        console.log('Service Worker: Limpiando cache antiguo:', cache);
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
    return self.clients.claim(); // Tomar control inmediato de las páginas
});

// Evento fetch: intercepta las peticiones de red
self.addEventListener('fetch', event => {
    console.log('Service Worker: Fetching', event.request.url);
    // Estrategia: Network falling back to Cache
    event.respondWith(
        fetch(event.request).catch(() => {
            // Si la petición de red falla, intenta servir desde el cache
            return caches.match(event.request).then(response => {
                if (response) {
                    return response;
                }
                // Si el recurso no está en cache, muestra la página offline
                // Solo para peticiones de navegación
                if (event.request.mode === 'navigate') {
                    return caches.match('/offline.html');
                }
            });
        })
    );
});

// --- SINCRONIZACIÓN PERIÓDICA EN SEGUNDO PLANO ---

self.addEventListener('periodicsync', event => {
    if (event.tag === 'update-location-sync') {
        console.log('Service Worker: Disparado evento de sincronización periódica de ubicación.');
        event.waitUntil(updateLocationInBackground());
    }
});

async function updateLocationInBackground() {
    console.log('Service Worker: Intentando obtener ubicación en segundo plano...');
    
    // Obtener la ubicación
    const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, { 
            enableHighAccuracy: true,
            timeout: 10000 // 10 segundos de tiempo de espera
        });
    }).catch(err => {
        console.error('Service Worker: Error al obtener geolocalización en segundo plano:', err.message);
        return null;
    });

    if (position) {
        const { latitude, longitude } = position.coords;
        console.log(`Service Worker: Ubicación obtenida en segundo plano: ${latitude}, ${longitude}`);

        // Enviar la ubicación al backend
        try {
            const response = await fetch('/api/actualizar_ubicacion/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    latitude: latitude, 
                    longitude: longitude 
                })
            });

            if (response.ok) {
                console.log('Service Worker: Ubicación enviada al backend con éxito desde segundo plano.');
            } else {
                console.error('Service Worker: Fallo al enviar ubicación al backend. Estado:', response.status);
            }
        } catch (error) {
            console.error('Service Worker: Error de red al enviar ubicación desde segundo plano:', error);
    }
}

// --- MANEJO DE NOTIFICACIONES PUSH ---

self.addEventListener('push', event => {
    console.log('Service Worker: Notificación Push recibida.');
    let data = {};
    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            console.error('Error al parsear JSON de la notificación push:', e);
            data = { title: 'Notificación', body: event.data.text() };
        }
    }

    const title = data.title || "De Aquí P-Allá";
    const options = {
        body: data.body || 'Tienes una nueva notificación.',
        icon: data.icon || '/static/imagenes/logo1.png',
        badge: '/static/imagenes/favicon.ico',
        data: {
            url: data.url || '/' // URL a abrir al hacer clic
        }
    };

    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', event => {
    console.log('Service Worker: Clic en notificación recibido.');
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});
