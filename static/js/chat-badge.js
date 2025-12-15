/**
 * Chat Badge Manager - Actualiza el badge cuando se leen mensajes
 */

// Función para marcar mensajes como leídos y actualizar badge
async function markMessagesAsRead(senderId) {
    try {
        const response = await fetch('/api/mark-messages-read/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                sender_id: senderId
            })
        });

        if (response.ok) {
            const data = await response.json();
            console.log(`✅ ${data.marked} mensajes marcados como leídos`);
            
            // Actualizar el badge
            if (window.badgeManager) {
                await window.badgeManager.fetchCount();
            }
        }
    } catch (error) {
        console.error('Error al marcar mensajes como leídos:', error);
    }
}

// Función para obtener cookie CSRF
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

// Auto-marcar mensajes como leídos cuando se abre una conversación
// Detectar cuando el usuario selecciona un contacto en el chat
document.addEventListener('DOMContentLoaded', function() {
    
    // Para el panel de comunicación de conductores
    const contactButtons = document.querySelectorAll('.contact-item, .user-item, [data-user-id]');
    
    contactButtons.forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id') || 
                          this.getAttribute('data-driver-id') ||
                          this.getAttribute('data-customer-id');
            
            if (userId) {
                // Esperar un poco para que se cargue la conversación
                setTimeout(() => {
                    markMessagesAsRead(userId);
                }, 1000);
            }
        });
    });
    
    // Para el detalle de carrera (chat con cliente/conductor)
    const rideId = document.querySelector('[data-ride-id]')?.getAttribute('data-ride-id');
    if (rideId) {
        // Obtener el ID del otro usuario (conductor o cliente)
        const otherUserId = document.querySelector('[data-other-user-id]')?.getAttribute('data-other-user-id');
        if (otherUserId) {
            markMessagesAsRead(otherUserId);
        }
    }
    
    // Actualizar badge cada vez que se envía un mensaje
    const chatForms = document.querySelectorAll('form[data-chat-form]');
    chatForms.forEach(form => {
        form.addEventListener('submit', function() {
            // Actualizar badge después de enviar mensaje
            setTimeout(() => {
                if (window.badgeManager) {
                    window.badgeManager.fetchCount();
                }
            }, 1500);
        });
    });
});

// Actualizar badge cuando se recibe un mensaje nuevo (via WebSocket)
// Interceptar todos los mensajes del WebSocket de chat
document.addEventListener('DOMContentLoaded', function() {
    // Esperar a que el WebSocket se conecte
    setTimeout(() => {
        if (typeof chatSocket !== 'undefined' && chatSocket) {
            console.log('💬 Interceptando mensajes de WebSocket para actualizar badge');
            
            const originalOnMessage = chatSocket.onmessage;
            chatSocket.onmessage = function(e) {
                const data = JSON.parse(e.data);
                
                // Si el mensaje incluye update_badge, actualizar el badge
                if (data.update_badge && data.badge_count !== undefined) {
                    if (window.badgeManager) {
                        window.badgeManager.set(data.badge_count);
                        console.log(`📛 Badge actualizado vía WebSocket: ${data.badge_count}`);
                    }
                }
                
                // Llamar al handler original
                if (originalOnMessage) {
                    originalOnMessage.call(this, e);
                }
            };
        }
    }, 1000);
});

// Exportar funciones para uso global
window.markMessagesAsRead = markMessagesAsRead;

console.log('💬 Chat Badge Manager cargado');
