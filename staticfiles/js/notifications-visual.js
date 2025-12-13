/**
 * Sistema de Notificaciones Visuales v1.0
 * De Aquí Pa'llá - Indicadores visuales para notificaciones push
 */

class NotificationManager {
    constructor() {
        this.notificationCount = 0;
        this.init();
    }

    init() {
        this.createToastContainer();
        this.setupNotificationBell();
        this.listenForServiceWorkerMessages();
    }

    createToastContainer() {
        if (!document.getElementById('toast-container')) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
    }

    setupNotificationBell() {
        document.addEventListener('DOMContentLoaded', () => {
            const notificationBell = document.getElementById('notification-bell');
            if (notificationBell) {
                notificationBell.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.clearNotifications();
                    console.log('🔔 Notificaciones limpiadas desde el bell');
                });
            }
        });
    }

    updateNotificationIndicator() {
        const indicator = document.getElementById('notification-indicator');
        const countElement = document.getElementById('notification-count');
        
        if (indicator && countElement) {
            if (this.notificationCount > 0) {
                indicator.style.display = 'block';
                countElement.textContent = this.notificationCount;
            } else {
                indicator.style.display = 'none';
            }
        }
    }

    showNotificationToast(title, message, type = 'primary') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;
        
        const toastElement = document.createElement('div');
        toastElement.className = `toast show align-items-center text-white bg-${type} border-0`;
        toastElement.setAttribute('role', 'alert');
        toastElement.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <strong>📱 ${title}</strong><br>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toastElement);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toastElement.parentNode) {
                toastElement.remove();
            }
        }, 5000);

        // Increment notification count
        this.notificationCount++;
        this.updateNotificationIndicator();

        // Vibrate if supported
        if ('vibrate' in navigator) {
            navigator.vibrate([200, 100, 200]);
        }

        console.log('🔔 Toast mostrado:', title, message);
    }

    clearNotifications() {
        const hadNotifications = this.notificationCount > 0;
        this.notificationCount = 0;
        this.updateNotificationIndicator();
        
        // Remove all toasts
        const toasts = document.querySelectorAll('.toast');
        toasts.forEach(toast => toast.remove());
        
        if (hadNotifications) {
            // Mostrar confirmación visual temporal
            this.showConfirmationMessage('🧹 Notificaciones limpiadas');
        }
        
        console.log('🧹 Notificaciones limpiadas');
    }

    showConfirmationMessage(message) {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;
        
        const toastElement = document.createElement('div');
        toastElement.className = 'toast show align-items-center text-white bg-info border-0';
        toastElement.setAttribute('role', 'alert');
        toastElement.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        toastContainer.appendChild(toastElement);
        
        // Auto-remove after 2 seconds (shorter than normal notifications)
        setTimeout(() => {
            if (toastElement.parentNode) {
                toastElement.remove();
            }
        }, 2000);
    }

    listenForServiceWorkerMessages() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.addEventListener('message', (event) => {
                if (event.data && event.data.type === 'PUSH_RECEIVED') {
                    const { title, body } = event.data;
                    this.showNotificationToast(
                        title || 'Nueva notificación', 
                        body || 'Tienes una notificación pendiente',
                        'success'
                    );
                }
            });
        }
    }

    // Método público para mostrar notificaciones desde otras partes de la aplicación
    showNotification(title, message, type = 'info') {
        this.showNotificationToast(title, message, type);
    }
}

// Inicializar el manejador de notificaciones
window.addEventListener('DOMContentLoaded', () => {
    window.notificationManager = new NotificationManager();
});

// Exportar para uso global
window.NotificationManager = NotificationManager;

console.log('✅ Sistema de notificaciones visuales cargado');