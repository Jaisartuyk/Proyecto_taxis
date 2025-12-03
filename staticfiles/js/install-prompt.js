// Script para mostrar prompt de instalación de PWA
let deferredPrompt;
let installButton;

window.addEventListener('DOMContentLoaded', () => {
    // Crear botón de instalación (oculto por defecto)
    createInstallButton();
});

// Escuchar el evento beforeinstallprompt
window.addEventListener('beforeinstallprompt', (e) => {
    console.log('PWA instalable detectada');
    
    // Prevenir el prompt automático
    e.preventDefault();
    
    // Guardar el evento para usarlo después
    deferredPrompt = e;
    
    // Mostrar el botón de instalación
    if (installButton) {
        installButton.style.display = 'block';
    }
});

// Crear botón de instalación
function createInstallButton() {
    // Verificar si ya está instalada
    if (window.matchMedia('(display-mode: standalone)').matches) {
        console.log('App ya instalada');
        return;
    }

    // Crear el botón
    installButton = document.createElement('button');
    installButton.id = 'install-pwa-button';
    installButton.innerHTML = '📱 Instalar App';
    installButton.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 25px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(74, 144, 226, 0.4);
        z-index: 9999;
        display: none;
        transition: all 0.3s ease;
    `;

    // Efectos hover
    installButton.addEventListener('mouseenter', () => {
        installButton.style.transform = 'scale(1.05)';
        installButton.style.boxShadow = '0 6px 20px rgba(74, 144, 226, 0.6)';
    });

    installButton.addEventListener('mouseleave', () => {
        installButton.style.transform = 'scale(1)';
        installButton.style.boxShadow = '0 4px 15px rgba(74, 144, 226, 0.4)';
    });

    // Click en el botón
    installButton.addEventListener('click', async () => {
        if (!deferredPrompt) {
            console.log('No hay prompt disponible');
            return;
        }

        // Mostrar el prompt de instalación
        deferredPrompt.prompt();

        // Esperar la respuesta del usuario
        const { outcome } = await deferredPrompt.userChoice;
        console.log(`Usuario ${outcome === 'accepted' ? 'aceptó' : 'rechazó'} la instalación`);

        // Limpiar el prompt
        deferredPrompt = null;

        // Ocultar el botón
        installButton.style.display = 'none';
    });

    // Añadir el botón al body
    document.body.appendChild(installButton);
}

// Detectar cuando la app se instala
window.addEventListener('appinstalled', () => {
    console.log('¡PWA instalada exitosamente!');
    
    // Ocultar el botón
    if (installButton) {
        installButton.style.display = 'none';
    }

    // Opcional: Mostrar mensaje de éxito
    showInstallSuccessMessage();
});

// Mostrar mensaje de éxito
function showInstallSuccessMessage() {
    const message = document.createElement('div');
    message.innerHTML = '✅ ¡App instalada! Ahora puedes acceder desde tu pantalla de inicio';
    message.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: #4CAF50;
        color: white;
        padding: 15px 30px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4);
        z-index: 10000;
        font-size: 16px;
        animation: slideDown 0.3s ease;
    `;

    document.body.appendChild(message);

    // Remover después de 5 segundos
    setTimeout(() => {
        message.style.animation = 'slideUp 0.3s ease';
        setTimeout(() => message.remove(), 300);
    }, 5000);
}

// Añadir animaciones CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideDown {
        from {
            transform: translateX(-50%) translateY(-100%);
            opacity: 0;
        }
        to {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }
    }

    @keyframes slideUp {
        from {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }
        to {
            transform: translateX(-50%) translateY(-100%);
            opacity: 0;
        }
    }

    #install-pwa-button:active {
        transform: scale(0.95) !important;
    }
`;
document.head.appendChild(style);
