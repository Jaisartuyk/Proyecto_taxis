// Service Worker for Push Notifications
const CACHE_NAME = 'deaquipalla-v1';

self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  event.waitUntil(clients.claim());
});

// Handle push notifications
self.addEventListener('push', (event) => {
  console.log('Push notification received:', event);

  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    console.error('Error parsing push data:', e);
    data = {
      title: 'Nueva Notificación',
      body: 'Tienes un nuevo mensaje',
      icon: '/static/imagenes/DE_AQU_PALL_Logo.png'
    };
  }

  const title = data.title || 'De Aquí Pa\'llá';
  const options = {
    body: data.body || 'Nuevo mensaje',
    icon: data.icon || '/static/imagenes/DE_AQU_PALL_Logo.png',
    badge: data.badge || '/static/imagenes/logo1.png',
    vibrate: [200, 100, 200],
    data: data.data || {},
    tag: data.data?.type || 'general',
    requireInteraction: true,
    actions: [
      {
        action: 'open',
        title: 'Abrir'
      },
      {
        action: 'close',
        title: 'Cerrar'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event);
  event.notification.close();

  if (event.action === 'close') {
    return;
  }

  const urlToOpen = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Check if there's already a window open
        for (let client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            client.focus();
            client.navigate(urlToOpen);
            return;
          }
        }
        // If no window is open, open a new one
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});
