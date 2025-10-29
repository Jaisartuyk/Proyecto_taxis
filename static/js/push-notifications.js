/**
 * Sistema de Notificaciones Push PWA
 * Para conductores - Alertas de nuevas carreras
 */

class PushNotificationManager {
    constructor() {
        this.vapidPublicKey = null;
        this.subscription = null;
        this.isSupported = 'serviceWorker' in navigator && 'PushManager' in window;
    }

    /**
     * Inicializar sistema de notificaciones
     */
    async init() {
        if (!this.isSupported) {
            console.warn('⚠️ Push notifications no soportadas en este navegador');
            return false;
        }

        try {
            // Verificar permisos
            const permission = await Notification.requestPermission();
            
            if (permission === 'granted') {
                console.log('✅ Permisos de notificación concedidos');
                await this.subscribeToPush();
                return true;
            } else {
                console.warn('⚠️ Permisos de notificación denegados');
                return false;
            }
        } catch (error) {
            console.error('❌ Error al inicializar notificaciones:', error);
            return false;
        }
    }

    /**
     * Suscribirse a notificaciones push
     */
    async subscribeToPush() {
        try {
            const registration = await navigator.serviceWorker.ready;
            
            // Obtener suscripción existente
            let subscription = await registration.pushManager.getSubscription();
            
            if (!subscription) {
                // Crear nueva suscripción
                subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: this.urlBase64ToUint8Array(this.getVapidPublicKey())
                });
                
                console.log('✅ Nueva suscripción creada');
            }
            
            this.subscription = subscription;
            
            // Enviar suscripción al servidor
            await this.sendSubscriptionToServer(subscription);
            
            return subscription;
        } catch (error) {
            console.error('❌ Error al suscribirse a push:', error);
            throw error;
        }
    }

    /**
     * Enviar suscripción al servidor
     */
    async sendSubscriptionToServer(subscription) {
        try {
            const response = await fetch('/api/push/subscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    subscription: subscription.toJSON()
                })
            });

            if (response.ok) {
                console.log('✅ Suscripción enviada al servidor');
            } else {
                console.error('❌ Error al enviar suscripción:', response.status);
            }
        } catch (error) {
            console.error('❌ Error al enviar suscripción:', error);
        }
    }

    /**
     * Mostrar notificación local (para testing)
     */
    async showLocalNotification(title, options = {}) {
        if (!this.isSupported) {
            console.warn('⚠️ Notificaciones no soportadas');
            return;
        }

        try {
            const registration = await navigator.serviceWorker.ready;
            
            const defaultOptions = {
                icon: '/static/imagenes/icon-192x192.png',
                badge: '/static/imagenes/icon-72x72.png',
                vibrate: [200, 100, 200],
                tag: 'nueva-carrera',
                requireInteraction: true,
                actions: [
                    {
                        action: 'ver',
                        title: '👀 Ver carrera'
                    },
                    {
                        action: 'cerrar',
                        title: '✖️ Cerrar'
                    }
                ]
            };

            await registration.showNotification(title, {
                ...defaultOptions,
                ...options
            });

            console.log('✅ Notificación mostrada');
        } catch (error) {
            console.error('❌ Error al mostrar notificación:', error);
        }
    }

    /**
     * Convertir VAPID key de base64 a Uint8Array
     */
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    /**
     * Obtener VAPID public key (temporal - usar variable de entorno en producción)
     */
    getVapidPublicKey() {
        // Por ahora usamos una key temporal
        // En producción, esto debe venir del servidor
        return 'BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U';
    }

    /**
     * Obtener CSRF token
     */
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Desuscribirse de notificaciones
     */
    async unsubscribe() {
        try {
            if (this.subscription) {
                await this.subscription.unsubscribe();
                console.log('✅ Desuscrito de notificaciones');
            }
        } catch (error) {
            console.error('❌ Error al desuscribirse:', error);
        }
    }
}

// Instancia global
const pushNotificationManager = new PushNotificationManager();

// Exportar para uso global
window.pushNotificationManager = pushNotificationManager;

// Auto-inicializar si el usuario es conductor
document.addEventListener('DOMContentLoaded', () => {
    // Verificar si es conductor
    const userRole = document.body.dataset.userRole;
    
    if (userRole === 'driver') {
        console.log('👤 Usuario es conductor - Inicializando notificaciones push');
        
        // Esperar a que el usuario interactúe (requerido por algunos navegadores)
        const initButton = document.getElementById('enable-notifications-btn');
        if (initButton) {
            initButton.addEventListener('click', async () => {
                const success = await pushNotificationManager.init();
                if (success) {
                    initButton.textContent = '✅ Notificaciones activadas';
                    initButton.disabled = true;
                }
            });
        } else {
            // Auto-inicializar después de 2 segundos
            setTimeout(() => {
                pushNotificationManager.init();
            }, 2000);
        }
    }
});
