// Push Notifications Management
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

// Register Service Worker
async function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) {
        console.log('Service Worker not supported');
        return null;
    }

    try {
        const registration = await navigator.serviceWorker.register('/service-worker.js', {
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
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
        });

        console.log('Push subscription successful:', subscription);

        // Send subscription to server
        await fetch('/api/webpush/subscribe/', {
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
        console.error('Failed to subscribe to push notifications:', error);
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
        // Only initialize if user is logged in (check for user-specific element)
        if (document.querySelector('[data-user-id]')) {
            initializePushNotifications();
        }
    });
} else {
    if (document.querySelector('[data-user-id]')) {
        initializePushNotifications();
    }
}

// Export for manual initialization
window.initializePushNotifications = initializePushNotifications;
