/**
 * Badge Manager - Gestión de badges en el ícono de la PWA
 * Muestra el número de notificaciones pendientes
 */

class BadgeManager {
    constructor() {
        this.isSupported = 'setAppBadge' in navigator;
        this.currentCount = 0;
    }

    /**
     * Verifica si Badge API está soportada
     */
    isAvailable() {
        return this.isSupported;
    }

    /**
     * Actualiza el badge con un número
     */
    async set(count) {
        if (!this.isSupported) {
            console.log('Badge API no soportada en este navegador');
            return false;
        }

        try {
            if (count > 0) {
                await navigator.setAppBadge(count);
                this.currentCount = count;
                console.log(`✅ Badge actualizado: ${count}`);
            } else {
                await this.clear();
            }
            return true;
        } catch (error) {
            console.error('Error al actualizar badge:', error);
            return false;
        }
    }

    /**
     * Limpia el badge (lo pone en 0)
     */
    async clear() {
        if (!this.isSupported) {
            return false;
        }

        try {
            await navigator.clearAppBadge();
            this.currentCount = 0;
            console.log('✅ Badge limpiado');
            return true;
        } catch (error) {
            console.error('Error al limpiar badge:', error);
            return false;
        }
    }

    /**
     * Incrementa el badge en 1
     */
    async increment() {
        return await this.set(this.currentCount + 1);
    }

    /**
     * Decrementa el badge en 1
     */
    async decrement() {
        const newCount = Math.max(0, this.currentCount - 1);
        return await this.set(newCount);
    }

    /**
     * Obtiene el conteo actual desde el servidor
     */
    async fetchCount() {
        try {
            const response = await fetch('/api/badge-count/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                const data = await response.json();
                await this.set(data.count);
                return data.count;
            }
        } catch (error) {
            console.error('Error al obtener conteo de badge:', error);
        }
        return 0;
    }

    /**
     * Inicia actualización automática del badge cada X minutos
     */
    startAutoUpdate(intervalMinutes = 2) {
        // Actualizar inmediatamente
        this.fetchCount();

        // Actualizar periódicamente
        this.updateInterval = setInterval(() => {
            this.fetchCount();
        }, intervalMinutes * 60 * 1000);

        console.log(`🔄 Auto-actualización de badge iniciada (cada ${intervalMinutes} min)`);
    }

    /**
     * Detiene la actualización automática
     */
    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            console.log('⏹️ Auto-actualización de badge detenida');
        }
    }
}

// Crear instancia global
const badgeManager = new BadgeManager();

// Iniciar automáticamente si el usuario está autenticado
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        const userIdElement = document.querySelector('[data-user-id]');
        const userId = userIdElement?.getAttribute('data-user-id');
        
        if (userId && userId !== '' && userId !== 'None') {
            console.log('📛 Badge Manager: Iniciando para usuario', userId);
            badgeManager.startAutoUpdate(2); // Actualizar cada 2 minutos
        }
    });
} else {
    const userIdElement = document.querySelector('[data-user-id]');
    const userId = userIdElement?.getAttribute('data-user-id');
    
    if (userId && userId !== '' && userId !== 'None') {
        console.log('📛 Badge Manager: Iniciando para usuario', userId);
        badgeManager.startAutoUpdate(2);
    }
}

// Actualizar badge cuando la página gana foco
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        badgeManager.fetchCount();
    }
});

// Exportar para uso manual
window.badgeManager = badgeManager;
