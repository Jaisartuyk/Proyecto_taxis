// Push Notifications Management v4.0
// Actualizado: 2025-12-04 - Fix WhiteNoise cache issue
const VAPID_PUBLIC_KEY = document.querySelector('meta[name="vapid-public-key"]')?.content || '';

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

// Request notification permission
async function requestNotificationPermission() {
    if (!('Notification' in window)) {
        console.log('This browser does not support notifications');
        return false;
    }

    if (Notification.permission === 'granted') {
        return true;
    }

    if (Notification.permission !== 'denied') {
        const permission = await Notification.requestPermission();
        return permission === 'granted';
    }

    return false;
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

// Initialize push notifications
async function initializePushNotifications() {
    // Request permission
    const hasPermission = await requestNotificationPermission();
    if (!hasPermission) {
        console.log('Notification permission denied');
        return;
    }

    // Register Service Worker
    const registration = await registerServiceWorker();
    if (!registration) {
        console.log('Service Worker registration failed');
        return;
    }

    // Wait for Service Worker to be ready
    await navigator.serviceWorker.ready;

    // Subscribe to push
    await subscribeToPush(registration);
}

// Auto-initialize on page load for logged-in users
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        const userIdElement = document.querySelector('[data-user-id]');
        const userId = userIdElement?.getAttribute('data-user-id');
        console.log('DOMContentLoaded - User ID:', userId);
        
        // Only initialize if user is logged in and has a valid ID
        if (userId && userId !== '' && userId !== 'None') {
            console.log('Initializing push notifications for user:', userId);
            initializePushNotifications();
        } else {
            console.log('User not authenticated, skipping push notifications');
        }
    });
} else {
    const userIdElement = document.querySelector('[data-user-id]');
    const userId = userIdElement?.getAttribute('data-user-id');
    console.log('Document ready - User ID:', userId);
    
    // Only initialize if user is logged in and has a valid ID
    if (userId && userId !== '' && userId !== 'None') {
        console.log('Initializing push notifications for user:', userId);
        initializePushNotifications();
    } else {
        console.log('User not authenticated, skipping push notifications');
    }
}

// Export for manual initialization
window.initializePushNotifications = initializePushNotifications;
