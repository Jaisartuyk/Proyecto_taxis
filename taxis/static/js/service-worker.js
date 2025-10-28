const CACHE_NAME = 'taxi-app-v3';
const OFFLINE_URL = '/offline/';
const ASSETS_TO_CACHE = [
  '/',
  OFFLINE_URL,
  '/static/css/theme.css',
  '/static/js/main.js',
  '/static/js/comunicacion.js',
  '/static/js/notifications.js',
  '/static/imagenes/logo1.png'
];

// Install event - cache essential assets
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Instalando...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Cacheando recursos');
        return cache.addAll(ASSETS_TO_CACHE);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activando...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] Eliminando caché antigua:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - network first with cache fallback
self.addEventListener('fetch', (event) => {
  // Ignorar requests no-HTTP
  if (!event.request.url.startsWith('http')) {
    return;
  }

  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .catch(() => caches.match(OFFLINE_URL))
    );
  } else {
    event.respondWith(
      caches.match(event.request)
        .then((response) => {
          if (response) {
            return response;
          }
          return fetch(event.request).then((response) => {
            // Cachear dinámicamente recursos exitosos
            if (response && response.status === 200) {
              const responseClone = response.clone();
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(event.request, responseClone);
              });
            }
            return response;
          });
        })
        .catch(() => {
          // Fallback para imágenes
          if (event.request.destination === 'image') {
            return caches.match('/static/imagenes/logo1.png');
          }
        })
    );
  }
});

// Push notification event
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push recibido');
  
  let data = {};
  if (event.data) {
    data = event.data.json();
  }

  const title = data.title || 'De Aquí Pa\'llá';
  const options = {
    body: data.body || 'Nueva notificación',
    icon: '/static/imagenes/logo1.png',
    badge: '/static/imagenes/logo1.png',
    vibrate: [200, 100, 200],
    data: data,
    actions: data.actions || []
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notificación clickeada');
  event.notification.close();

  const urlToOpen = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Si ya hay una ventana abierta, enfocarla
        for (let client of clientList) {
          if (client.url === urlToOpen && 'focus' in client) {
            return client.focus();
          }
        }
        // Si no, abrir una nueva ventana
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Sync event para sincronización en background
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] Background sync:', event.tag);
  
  if (event.tag === 'sync-rides') {
    event.waitUntil(syncRides());
  }
});

async function syncRides() {
  try {
    // Sincronizar datos de carreras cuando haya conexión
    const response = await fetch('/api/rides/sync/');
    if (response.ok) {
      console.log('[Service Worker] Sincronización exitosa');
    }
  } catch (error) {
    console.error('[Service Worker] Error en sincronización:', error);
  }
}
