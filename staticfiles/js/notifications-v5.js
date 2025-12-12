// Push Notifications Management v5.3 - AUTO-SUSCRIPCIÓN AUTOMÁTICA
// Actualizado: 2025-12-11 - Suscripción automática sin intervención del usuario
const VAPID_PUBLIC_KEY = document.querySelector('meta[name="vapid-public-key"]')?.content || '';

// Estado de suscripción
let subscriptionCheckInterval = null;
let retryCount = 0;
const MAX_RETRIES = 3;

// Convert VAPID key from base64 to Uint8Array
function urlBase64ToUint8Array(base64String) {
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

// Request notification permission silently
async function requestNotificationPermission() {
    if (!('Notification' in window)) {
        console.log('❌ Este navegador no soporta notificaciones');
        return false;
    }

    // Si ya está granted, retornar true inmediatamente
    if (Notification.permission === 'granted') {
        console.log('✅ Permisos de notificación ya concedidos');
        return true;
    }

    // Si está denegado, no podemos hacer nada
    if (Notification.permission === 'denied') {
        console.log('❌ Permisos de notificación denegados por el usuario');
        return false;
    }

    // Si es "default", pedir permiso
    try {
        console.log('📱 Solicitando permisos de notificación...');
        const permission = await Notification.requestPermission();
        console.log('📱 Resultado del permiso:', permission);
        return permission === 'granted';
    } catch (error) {
        console.error('❌ Error al solicitar permisos:', error);
        return false;
    }
}

// Get existing Service Worker registration or register a new one
async function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) {
        console.log('Service Worker not supported');
        return null;
    }

    try {
        // Primero intentar obtener el registro existente
        let registration = await navigator.serviceWorker.getRegistration('/');
        
        if (registration) {
            console.log('Using existing Service Worker registration:', registration);
            return registration;
        }
        
        // Si no existe, registrar uno nuevo desde la raíz con scope correcto
        registration = await navigator.serviceWorker.register('/service-worker.js', {
            scope: '/'
        });
        console.log('Service Worker registered successfully:', registration);
        return registration;
    } catch (error) {
        console.error('Service Worker registration failed:', error);
        return null;
    }
}

// Subscribe to push notifications
async function subscribeToPush(registration) {
    try {
        // Primero, intentar eliminar cualquier suscripción existente
        const existingSubscription = await registration.pushManager.getSubscription();
        if (existingSubscription) {
            console.log('Eliminando suscripción antigua...');
            await existingSubscription.unsubscribe();
            console.log('Suscripción antigua eliminada');
        }

        // Crear nueva suscripción con las claves VAPID actuales
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
        });

        console.log('Push subscription successful:', subscription);

        // Send subscription to server
        await fetch('/api/save-subscription/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(subscription.toJSON())
        });

        console.log('Subscription sent to server');
        return subscription;
    } catch (error) {
        console.error('Push subscription failed:', error);
        return null;
    }
}

// Get CSRF token
function getCookie(name) {
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

// Initialize push notifications with retry logic
async function initializePushNotifications() {
    try {
        console.log('🚀 Iniciando proceso de suscripción...');
        
        // Request permission
        const hasPermission = await requestNotificationPermission();
        if (!hasPermission) {
            console.log('⚠️ Sin permisos de notificación, reintentando en 30 segundos...');
            
            // Reintentar después de 30 segundos
            if (retryCount < MAX_RETRIES) {
                retryCount++;
                setTimeout(() => {
                    console.log(`🔄 Reintento ${retryCount}/${MAX_RETRIES}...`);
                    initializePushNotifications();
                }, 30000);
            }
            return;
        }
        
        console.log('✅ Permisos concedidos, registrando Service Worker...');

        // Register Service Worker
        const registration = await registerServiceWorker();
        if (!registration) {
            console.log('❌ Fallo al registrar Service Worker');
            throw new Error('Service Worker registration failed');
        }

        // Wait for Service Worker to be ready
        await navigator.serviceWorker.ready;
        console.log('✅ Service Worker listo');

        // Subscribe to push
        await subscribeToPush(registration);
        
        // Resetear contador de reintentos en caso de éxito
        retryCount = 0;
        console.log('✅ Suscripción a push notifications completada exitosamente');
        
    } catch (error) {
        console.error('❌ Error al inicializar notificaciones push:', error);
        
        // Reintentar en caso de error
        if (retryCount < MAX_RETRIES) {
            retryCount++;
            console.log(`🔄 Reintentando en 30 segundos (${retryCount}/${MAX_RETRIES})...`);
            setTimeout(() => {
                initializePushNotifications();
            }, 30000);
        } else {
            console.error('❌ Máximo de reintentos alcanzado');
        }
    }
}

// Auto-initialize on page load for logged-in users
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeForUser);
} else {
    initializeForUser();
}

function initializeForUser() {
    const userIdElement = document.querySelector('[data-user-id]');
    const userId = userIdElement?.getAttribute('data-user-id');
    
    // Only initialize if user is logged in and has a valid ID
    if (userId && userId !== '' && userId !== 'None') {
        console.log('🔔 Inicializando notificaciones push para usuario:', userId);
        
        // Inicializar inmediatamente
        initializePushNotifications();
        
        // Verificar y re-suscribir cada 5 minutos
        subscriptionCheckInterval = setInterval(() => {
            console.log('🔄 Verificando estado de suscripción...');
            checkAndResubscribe();
        }, 5 * 60 * 1000); // 5 minutos
        
        // También verificar al hacer focus en la ventana
        window.addEventListener('focus', () => {
            console.log('👁️ Ventana enfocada, verificando suscripción...');
            setTimeout(checkAndResubscribe, 1000);
        });
        
    } else {
        console.log('⚠️ Usuario no autenticado, notificaciones deshabilitadas');
    }
}

// Verificar y re-suscribir si es necesario
async function checkAndResubscribe() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        return;
    }
    
    try {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();
        
        if (!subscription) {
            console.log('⚠️ Suscripción perdida, re-suscribiendo automáticamente...');
            await initializePushNotifications();
        } else {
            console.log('✅ Suscripción activa:', subscription.endpoint.substring(0, 50) + '...');
        }
    } catch (error) {
        console.error('❌ Error al verificar suscripción:', error);
    }
}

// Export for manual initialization
window.initializePushNotifications = initializePushNotifications;
window.checkAndResubscribe = checkAndResubscribe;
