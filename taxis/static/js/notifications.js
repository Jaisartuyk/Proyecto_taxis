// Sistema de notificaciones para PWA
class NotificationManager {
    constructor() {
        this.permission = Notification.permission;
        this.isSupported = 'Notification' in window;
    }

    async requestPermission() {
        if (!this.isSupported) {
            console.log('Las notificaciones no están soportadas en este navegador');
            return false;
        }

        if (this.permission === 'granted') {
            return true;
        }

        if (this.permission !== 'denied') {
            const permission = await Notification.requestPermission();
            this.permission = permission;
            return permission === 'granted';
        }

        return false;
    }

    async showNotification(title, options = {}) {
        const hasPermission = await this.requestPermission();
        
        if (!hasPermission) {
            console.log('Permiso de notificación denegado');
            return;
        }

        const defaultOptions = {
            icon: '/static/imagenes/logo1.png',
            badge: '/static/imagenes/logo1.png',
            vibrate: [200, 100, 200],
            tag: 'taxi-notification',
            requireInteraction: false,
            ...options
        };

        // Si hay service worker registrado, usar su API
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            const registration = await navigator.serviceWorker.ready;
            return registration.showNotification(title, defaultOptions);
        }

        // Fallback a notificación normal
        return new Notification(title, defaultOptions);
    }

    notifyNewRide(rideData) {
        this.showNotification('Nueva carrera disponible', {
            body: `Desde: ${rideData.pickup}\nHasta: ${rideData.destination}`,
            icon: '/static/imagenes/logo1.png',
            tag: `ride-${rideData.id}`,
            data: { type: 'new_ride', rideId: rideData.id }
        });
    }

    notifyRideAccepted(rideData) {
        this.showNotification('Carrera aceptada', {
            body: `El conductor ${rideData.driverName} ha aceptado tu carrera`,
            icon: '/static/imagenes/logo1.png',
            tag: `ride-accepted-${rideData.id}`,
            data: { type: 'ride_accepted', rideId: rideData.id }
        });
    }

    notifyDriverArriving(rideData) {
        this.showNotification('Conductor cerca', {
            body: `Tu conductor está llegando en ${rideData.eta} minutos`,
            icon: '/static/imagenes/logo1.png',
            tag: `driver-arriving-${rideData.id}`,
            requireInteraction: true,
            data: { type: 'driver_arriving', rideId: rideData.id }
        });
    }

    notifyAudioMessage(senderName) {
        this.showNotification('Nuevo mensaje de audio', {
            body: `${senderName} te ha enviado un mensaje de voz`,
            icon: '/static/imagenes/logo1.png',
            tag: 'audio-message',
            data: { type: 'audio_message', sender: senderName }
        });
    }
}

// Exportar instancia única
const notificationManager = new NotificationManager();

// Solicitar permisos al cargar la página (solo si el usuario está autenticado)
document.addEventListener('DOMContentLoaded', () => {
    // Esperar un poco antes de solicitar permisos para no ser intrusivo
    setTimeout(() => {
        if (document.querySelector('[data-user-authenticated="true"]')) {
            notificationManager.requestPermission();
        }
    }, 3000);
});

// Hacer disponible globalmente
window.notificationManager = notificationManager;
