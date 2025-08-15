// static/js/helmet-app.js - Sistema de Detección de Cascos

/**
 * Clase principal para manejar la aplicación de detección de cascos
 */
class HelmetDetectionApp {
    constructor() {
        // Estado de la aplicación
        this.isDetectionActive = false;
        this.isConnected = false;
        
        // Intervalos para actualizaciones
        this.updateInterval = null;
        this.logsInterval = null;
        
        // Configuración
        this.config = {
            frameUpdateInterval: 100,  // 100ms = 10 FPS
            logsUpdateInterval: 2000,  // 2 segundos
            buttonCooldown: 1000,      // 1 segundo entre clicks
            notificationDuration: 4000  // 4 segundos
        };
        
        // Inicializar aplicación
        this.init();
    }

    /**
     * Inicializa la aplicación
     */
    init() {
        this.initializeElements();
        this.setupEventListeners();
        this.startUpdates();
        this.log('Sistema iniciado correctamente');
    }

    /**
     * Inicializa referencias a elementos DOM
     */
    initializeElements() {
        this.elements = {
            // Video
            videoFeed: document.getElementById('videoFeed'),
            videoPlaceholder: document.getElementById('videoPlaceholder'),
            
            // Estados
            detectionStatus: document.getElementById('detectionStatus'),
            cameraStatus: document.getElementById('cameraStatus'),
            connectionStatus: document.getElementById('connectionStatus'),
            
            // Controles
            toggleDetection: document.getElementById('toggleDetection'),
            testNotification: document.getElementById('testNotification'),
            
            // Configuración
            chatId: document.getElementById('chatId'),
            updateChatId: document.getElementById('updateChatId'),
            
            // Logs y estadísticas
            logsContainer: document.getElementById('logsContainer'),
            stats: {
                totalDetections: document.getElementById('totalDetections'),
                violations: document.getElementById('violations'),
                notifications: document.getElementById('notifications'),
                uptime: document.getElementById('uptime')
            }
        };

        // Verificar que todos los elementos existen
        this.validateElements();
    }

    /**
     * Valida que todos los elementos DOM necesarios existan
     */
    validateElements() {
        const missingElements = [];
        
        for (const [key, element] of Object.entries(this.elements)) {
            if (key === 'stats') {
                for (const [statKey, statElement] of Object.entries(element)) {
                    if (!statElement) {
                        missingElements.push(`stats.${statKey}`);
                    }
                }
            } else if (!element) {
                missingElements.push(key);
            }
        }

        if (missingElements.length > 0) {
            console.error('Elementos DOM faltantes:', missingElements);
        }
    }

    /**
     * Configura los event listeners
     */
    setupEventListeners() {
        // Botones principales
        this.elements.toggleDetection?.addEventListener('click', 
            () => this.toggleDetection());
        
        this.elements.testNotification?.addEventListener('click', 
            () => this.testNotification());
        
        this.elements.updateChatId?.addEventListener('click', 
            () => this.updateChatId());

        // Eventos de teclado
        this.elements.chatId?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.updateChatId();
            }
        });

        // Eventos de visibilidad de página
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseUpdates();
            } else {
                this.resumeUpdates();
            }
        });
    }

    /**
     * Inicia las actualizaciones automáticas
     */
    startUpdates() {
        // Detener actualizaciones previas si existen
        this.stopUpdates();

        // Actualizar frames
        this.updateInterval = setInterval(() => {
            this.updateFrame();
        }, this.config.frameUpdateInterval);
        
        // Actualizar logs
        this.logsInterval = setInterval(() => {
            this.updateLogs();
        }, this.config.logsUpdateInterval);
        
        // Primera actualización inmediata
        this.updateFrame();
        this.updateLogs();
        
        this.log('Actualizaciones automáticas iniciadas');
    }

    /**
     * Detiene las actualizaciones automáticas
     */
    stopUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        if (this.logsInterval) {
            clearInterval(this.logsInterval);
            this.logsInterval = null;
        }
    }

    /**
     * Pausa las actualizaciones (cuando la página no está visible)
     */
    pauseUpdates() {
        this.stopUpdates();
        this.log('Actualizaciones pausadas');
    }

    /**
     * Reanuda las actualizaciones
     */
    resumeUpdates() {
        this.startUpdates();
        this.log('Actualizaciones reanudadas');
    }

    /**
     * Actualiza el frame del video
     */
    async updateFrame() {
        try {
            const response = await fetch('/api/frame');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            if (data.frame) {
                // Actualizar imagen
                this.elements.videoFeed.src = `data:image/jpeg;base64,${data.frame}`;
                this.elements.videoFeed.style.display = 'block';
                this.elements.videoPlaceholder.style.display = 'none';
                
                // Actualizar estados
                this.isDetectionActive = data.detection_active;
                this.updateDetectionStatus(data.detection_active, data.violation);
                
                // Actualizar estadísticas
                if (data.stats) {
                    this.updateStats(data.stats);
                }
                
                // Marcar como conectado
                this.setConnectionStatus(true);
            }
            
        } catch (error) {
            console.error('Error actualizando frame:', error);
            this.setConnectionStatus(false);
            this.handleConnectionError(error);
        }
    }

    /**
     * Actualiza los logs de actividad
     */
    async updateLogs() {
        try {
            const response = await fetch('/api/logs');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const logs = await response.json();
            this.updateLogsDisplay(logs);
            
        } catch (error) {
            console.error('Error actualizando logs:', error);
        }
    }

    /**
     * Maneja errores de conexión
     */
    handleConnectionError(error) {
        // Si hay muchos errores consecutivos, reducir frecuencia de actualizaciones
        if (!this.isConnected) {
            this.config.frameUpdateInterval = Math.min(this.config.frameUpdateInterval * 1.5, 5000);
            this.startUpdates(); // Reiniciar con nueva frecuencia
        }
    }

    /**
     * Establece el estado de conexión
     */
    setConnectionStatus(connected) {
        if (this.isConnected !== connected) {
            this.isConnected = connected;
            const statusEl = this.elements.connectionStatus;
            
            if (connected) {
                statusEl.className = 'connection-status connected';
                statusEl.innerHTML = '<i class="fas fa-circle"></i> Conectado';
                
                // Restaurar frecuencia normal si estaba reducida
                this.config.frameUpdateInterval = 100;
            } else {
                statusEl.className = 'connection-status disconnected';
                statusEl.innerHTML = '<i class="fas fa-circle"></i> Desconectado';
            }
        }
    }

    /**
     * Actualiza el estado de detección visual
     */
    updateDetectionStatus(isActive, hasViolation) {
        const statusElement = this.elements.detectionStatus;
        const buttonElement = this.elements.toggleDetection;

        if (!statusElement || !buttonElement) return;

        if (isActive) {
            if (hasViolation) {
                statusElement.className = 'status-badge status-danger';
                statusElement.innerHTML = '<i class="fas fa-exclamation-triangle pulse"></i> VIOLACIÓN DETECTADA';
            } else {
                statusElement.className = 'status-badge status-active';
                statusElement.innerHTML = '<i class="fas fa-check-circle"></i> DETECCIÓN ACTIVA';
            }
            
            buttonElement.innerHTML = '<i class="fas fa-pause"></i> Desactivar Detección';
            buttonElement.className = 'control-button btn-danger';
        } else {
            statusElement.className = 'status-badge status-inactive';
            statusElement.innerHTML = '<i class="fas fa-times-circle"></i> DETECCIÓN INACTIVA';
            
            buttonElement.innerHTML = '<i class="fas fa-play"></i> Activar Detección';
            buttonElement.className = 'control-button btn-primary';
        }
    }

    /**
     * Actualiza las estadísticas
     */
    updateStats(stats) {
        if (!stats) return;

        // Actualizar valores
        if (this.elements.stats.totalDetections) {
            this.elements.stats.totalDetections.textContent = stats.total_detections || 0;
        }
        
        if (this.elements.stats.violations) {
            this.elements.stats.violations.textContent = stats.violations_detected || 0;
        }
        
        if (this.elements.stats.notifications) {
            this.elements.stats.notifications.textContent = stats.notifications_sent || 0;
        }
        
        // Formatear tiempo de actividad
        if (this.elements.stats.uptime && stats.uptime) {
            const hours = Math.floor(stats.uptime / 3600);
            const minutes = Math.floor((stats.uptime % 3600) / 60);
            this.elements.stats.uptime.textContent = 
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
        }
    }

    /**
     * Actualiza la visualización de logs
     */
    updateLogsDisplay(logs) {
        if (!this.elements.logsContainer || !Array.isArray(logs)) return;

        // Limpiar contenedor
        this.elements.logsContainer.innerHTML = '';
        
        // Agregar cada log
        logs.forEach(log => {
            const logElement = document.createElement('div');
            logElement.className = 'log-entry';
            logElement.innerHTML = `
                <span class="log-timestamp">${this.escapeHtml(log.timestamp)}</span>
                <span class="log-level log-${log.level.toLowerCase()}">${this.escapeHtml(log.level)}</span>
                <span>${this.escapeHtml(log.message)}</span>
            `;
            this.elements.logsContainer.appendChild(logElement);
        });
    }

    /**
     * Activa/desactiva la detección
     */
    async toggleDetection() {
        if (this.elements.toggleDetection.disabled) return;

        try {
            this.setButtonLoading(this.elements.toggleDetection, true);
            
            const response = await fetch('/api/toggle_detection', { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.isDetectionActive = data.detection_active;
            
            // Actualizar inmediatamente
            this.updateFrame();
            
            const status = data.detection_active ? 'activada' : 'desactivada';
            this.showNotification(`Detección ${status} correctamente`, 'success');
            
        } catch (error) {
            console.error('Error cambiando estado de detección:', error);
            this.showNotification('Error al cambiar estado de detección', 'error');
        } finally {
            setTimeout(() => {
                this.setButtonLoading(this.elements.toggleDetection, false);
            }, this.config.buttonCooldown);
        }
    }

    /**
     * Envía notificación de prueba
     */
    async testNotification() {
        if (this.elements.testNotification.disabled) return;

        try {
            this.setButtonLoading(this.elements.testNotification, true, 
                '<i class="fas fa-spinner fa-spin"></i> Enviando...');
            
            const response = await fetch('/api/test_notification', { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Notificación de prueba enviada correctamente', 'success');
            } else {
                this.showNotification(`Error: ${data.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Error enviando notificación de prueba:', error);
            this.showNotification('Error al enviar notificación de prueba', 'error');
        } finally {
            setTimeout(() => {
                this.setButtonLoading(this.elements.testNotification, false,
                    '<i class="fas fa-bell"></i> Probar Notificación');
            }, 2000);
        }
    }

    /**
     * Actualiza el Chat ID
     */
    async updateChatId() {
        const chatId = this.elements.chatId?.value?.trim();
        
        if (!chatId) {
            this.showNotification('Por favor ingrese un Chat ID válido', 'error');
            return;
        }

        if (this.elements.updateChatId.disabled) return;

        try {
            this.setButtonLoading(this.elements.updateChatId, true,
                '<i class="fas fa-spinner fa-spin"></i> Guardando...');
            
            const response = await fetch('/api/update_chat_id', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ chat_id: chatId })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Chat ID actualizado correctamente en config.py', 'success');
            } else {
                this.showNotification(`Error: ${data.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Error actualizando Chat ID:', error);
            this.showNotification('Error al actualizar Chat ID', 'error');
        } finally {
            setTimeout(() => {
                this.setButtonLoading(this.elements.updateChatId, false,
                    '<i class="fas fa-save"></i> Guardar Chat ID');
            }, 2000);
        }
    }

    /**
     * Establece el estado de carga de un botón
     */
    setButtonLoading(button, loading, customText = null) {
        if (!button) return;

        button.disabled = loading;
        
        if (loading && customText) {
            button.innerHTML = customText;
        }
    }

    /**
     * Muestra una notificación
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 60px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 10px;
            color: white;
            font-weight: 600;
            z-index: 1000;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
            max-width: 400px;
            word-wrap: break-word;
        `;
        
        const colors = {
            success: 'linear-gradient(135deg, #34d399, #10b981)',
            error: 'linear-gradient(135deg, #f87171, #ef4444)',
            warning: 'linear-gradient(135deg, #fbbf24, #f59e0b)',
            info: 'linear-gradient(135deg, #60a5fa, #3b82f6)'
        };
        
        notification.style.background = colors[type] || colors.info;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Animar entrada
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Animar salida y remover
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, this.config.notificationDuration);
    }

    /**
     * Escapa HTML para prevenir XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Log interno para debugging
     */
    log(message) {
        console.log(`[HelmetApp] ${message}`);
    }

    /**
     * Destruye la aplicación y limpia recursos
     */
    destroy() {
        this.stopUpdates();
        this.log('Aplicación destruida');
    }
}

// ===== INICIALIZACIÓN AUTOMÁTICA =====

// Variable global para acceso desde consola (debugging)
let helmetApp = null;

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    try {
        helmetApp = new HelmetDetectionApp();
        console.log('✅ Aplicación de detección de cascos iniciada correctamente');
    } catch (error) {
        console.error('❌ Error iniciando aplicación:', error);
    }
});

// Limpiar recursos cuando se cierre la página
window.addEventListener('beforeunload', () => {
    if (helmetApp) {
        helmetApp.destroy();
    }
});

// Exponer API pública para debugging/testing
window.HelmetDetectionAPI = {
    /**
     * Obtiene la instancia actual de la aplicación
     */
    getInstance: () => helmetApp,
    
    /**
     * Fuerza una actualización del frame
     */
    forceUpdate: () => {
        if (helmetApp) {
            helmetApp.updateFrame();
        }
    },
    
    /**
     * Obtiene el estado actual
     */
    getStatus: () => {
        if (!helmetApp) return null;
        return {
            isConnected: helmetApp.isConnected,
            isDetectionActive: helmetApp.isDetectionActive,
            config: helmetApp.config
        };
    },
    
    /**
     * Muestra una notificación personalizada
     */
    showNotification: (message, type = 'info') => {
        if (helmetApp) {
            helmetApp.showNotification(message, type);
        }
    }
};