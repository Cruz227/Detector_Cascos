# app.py - Backend Flask modular para Sistema de Detección de Cascos
from flask import Flask, render_template, request, jsonify, send_from_directory
import cv2
import time
import threading
import base64
from datetime import datetime
import json
import re
import os

# Importar nuestros módulos existentes
import config
from detector import HelmetDetector
from notifier import TelegramNotifier

# Configuración de la aplicación Flask
app = Flask(__name__)
app.config.update({
    'SECRET_KEY': 'helmet_detection_secret_key_2024',
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max file size
    'JSON_SORT_KEYS': False
})

class ConfigManager:
    """Clase para manejar la actualización del archivo config.py de forma segura"""
    
    @staticmethod
    def backup_config():
        """Crea un backup del archivo config.py"""
        try:
            import shutil
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f'config_backup_{timestamp}.py'
            shutil.copy2('config.py', backup_path)
            return backup_path
        except Exception as e:
            print(f"⚠️ No se pudo crear backup: {e}")
            return None
    
    @staticmethod
    def update_chat_id(new_chat_id):
        """Actualiza el CHAT_ID en el archivo config.py de forma segura"""
        try:
            config_path = 'config.py'
            
            # Crear backup antes de modificar
            backup_path = ConfigManager.backup_config()
            
            # Leer el archivo actual
            with open(config_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Buscar y reemplazar la línea CHAT_ID
            pattern = r'CHAT_ID\s*=\s*["\'].*?["\']'
            replacement = f'CHAT_ID = "{new_chat_id}"'
            
            if re.search(pattern, content):
                new_content = re.sub(pattern, replacement, content)
            else:
                # Agregar si no existe
                new_content = content.rstrip() + f'\n\n# Actualizado automáticamente desde web\nCHAT_ID = "{new_chat_id}"\n'
            
            # Escribir el archivo actualizado
            with open(config_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
            
            # Actualizar el módulo config en memoria
            config.CHAT_ID = new_chat_id
            
            print(f"✅ Config.py actualizado con nuevo Chat ID: {new_chat_id}")
            if backup_path:
                print(f"📁 Backup creado: {backup_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando config.py: {e}")
            return False

class WebHelmetSystem:
    """Sistema principal de detección de cascos para web"""
    
    def __init__(self):
        print("🔧 Inicializando WebHelmetSystem...")
        
        # Estado del sistema
        self.is_detection_active = False
        self.current_chat_id = config.CHAT_ID
        self.last_notification_time = 0
        
        # Control de hilos
        self.running = False
        self.camera_thread = None
        self.frame_lock = threading.Lock()
        
        # Video y detección
        self.cap = None
        self.current_frame = None
        self.current_violation = False
        
        # Estadísticas
        self.stats = {
            'total_detections': 0,
            'violations_detected': 0,
            'notifications_sent': 0,
            'uptime_start': time.time()
        }
        
        # Logs
        self.logs = []
        self.max_logs = 100
        self.logs_lock = threading.Lock()
        
        # Inicializar componentes
        self.init_detector()
        self.init_notifier()
        self.start_camera()
    
    def init_detector(self):
        """Inicializa el detector YOLO"""
        try:
            self.detector = HelmetDetector(config.MODEL_PATH)
            print("✅ Detector YOLO inicializado correctamente")
            self.log_event("SYSTEM", "Detector YOLO inicializado")
        except Exception as e:
            print(f"❌ Error inicializando detector: {e}")
            self.detector = None
            self.log_event("ERROR", f"Error inicializando detector: {e}")
    
    def init_notifier(self):
        """Inicializa el notificador de Telegram"""
        try:
            self.notifier = TelegramNotifier(config.BOT_TOKEN, config.CHAT_ID)
            print("✅ Notificador de Telegram inicializado")
            self.log_event("SYSTEM", "Notificador de Telegram inicializado")
        except Exception as e:
            print(f"❌ Error inicializando notificador: {e}")
            self.notifier = None
            self.log_event("ERROR", f"Error inicializando notificador: {e}")
    
    def start_camera(self):
        """Inicializa y configura la cámara"""
        print("📹 Iniciando sistema de cámara...")
        
        try:
            source = config.WEBCAM_ID if config.USE_WEBCAM else config.VIDEO_PATH
            print(f"📹 Fuente configurada: {source}")
            
            self.cap = cv2.VideoCapture(source)
            
            if not self.cap.isOpened():
                raise Exception(f"No se pudo abrir la fuente de video: {source}")
            
            # Configurar propiedades de la cámara
            if config.USE_WEBCAM:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            print("✅ Cámara inicializada correctamente")
            self.log_event("SYSTEM", f"Cámara iniciada - Fuente: {source}")
            
            # Iniciar hilo de procesamiento
            self.running = True
            self.camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
            self.camera_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Error iniciando cámara: {e}")
            self.log_event("ERROR", f"Error iniciando cámara: {e}")
            return False
    
    def camera_loop(self):
        """Loop principal de procesamiento de video"""
        print("🎥 Iniciando loop de procesamiento de video...")
        frame_count = 0
        last_log_time = time.time()
        
        while self.running:
            try:
                if not self.cap or not self.cap.isOpened():
                    time.sleep(0.1)
                    continue
                
                ret, frame = self.cap.read()
                
                if not ret:
                    # Reiniciar video si es archivo
                    if not config.USE_WEBCAM:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    time.sleep(0.033)
                    continue
                
                frame_count += 1
                
                # Redimensionar para optimizar rendimiento
                height, width = frame.shape[:2]
                if width > 640:
                    scale = 640 / width
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    frame = cv2.resize(frame, (new_width, new_height))
                
                # Procesar detección solo si el detector está disponible
                violation_detected = False
                annotated_frame = frame.copy()
                
                if self.detector:
                    try:
                        results = self.detector.detect_on_frame(frame)
                        annotated_frame = self.detector.draw_detections(results)
                        
                        # Verificar violaciones si la detección está activa
                        if self.is_detection_active:
                            violation_detected = self.detector.find_violation(results, config.TARGET_CLASS_NAME)
                            self.stats['total_detections'] += 1
                            
                            if violation_detected:
                                self.stats['violations_detected'] += 1
                                self.handle_violation(annotated_frame)
                                
                    except Exception as e:
                        print(f"⚠️ Error en detección: {e}")
                        if frame_count % 100 == 0:  # Log cada 100 frames
                            self.log_event("ERROR", f"Error en detección: {e}")
                
                # Guardar frame actual de forma thread-safe
                with self.frame_lock:
                    try:
                        _, buffer = cv2.imencode('.jpg', annotated_frame, 
                                              [cv2.IMWRITE_JPEG_QUALITY, 85])
                        self.current_frame = base64.b64encode(buffer).decode('utf-8')
                        self.current_violation = violation_detected
                    except Exception as e:
                        print(f"⚠️ Error codificando frame: {e}")
                
                # Log periódico de estado
                current_time = time.time()
                if current_time - last_log_time > 60:  # Cada minuto
                    self.log_event("SYSTEM", f"Sistema funcionando - Frame {frame_count}")
                    last_log_time = current_time
                
                # Control de FPS
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"❌ Error en camera_loop: {e}")
                self.log_event("ERROR", f"Error en camera_loop: {e}")
                time.sleep(1)
    
    def handle_violation(self, frame):
        """Maneja una violación detectada"""
        current_time = time.time()
        
        if (current_time - self.last_notification_time) > config.NOTIFICATION_COOLDOWN_SECONDS:
            if self.send_notification(frame):
                self.last_notification_time = current_time
                self.stats['notifications_sent'] += 1
    
    def send_notification(self, frame):
        """Envía notificación a Telegram de forma asíncrona"""
        if not self.notifier or not self.notifier.bot:
            return False
        
        try:
            # Actualizar chat_id si cambió
            self.notifier.chat_id = self.current_chat_id
            
            # Enviar notificación en hilo separado
            threading.Thread(
                target=self._send_notification_async,
                args=(frame,),
                daemon=True
            ).start()
            
            self.log_event("NOTIFICATION", f"Alerta enviada a chat {self.current_chat_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error preparando notificación: {e}")
            self.log_event("ERROR", f"Error enviando notificación: {e}")
            return False
    
    def _send_notification_async(self, frame):
        """Envía la notificación de forma asíncrona"""
        try:
            self.notifier.send_alert(frame)
        except Exception as e:
            print(f"❌ Error en notificación asíncrona: {e}")
    
    def get_current_frame(self):
        """Obtiene el frame actual de forma thread-safe"""
        with self.frame_lock:
            return self.current_frame, self.current_violation
    
    def toggle_detection(self):
        """Activa/desactiva la detección"""
        self.is_detection_active = not self.is_detection_active
        status = "ACTIVADA" if self.is_detection_active else "DESACTIVADA"
        print(f"🔄 Detección {status}")
        self.log_event("SYSTEM", f"Detección {status}")
        return self.is_detection_active
    
    def update_chat_id(self, new_chat_id):
        """Actualiza el Chat ID tanto en memoria como en archivo"""
        old_chat_id = self.current_chat_id
        
        if ConfigManager.update_chat_id(new_chat_id):
            self.current_chat_id = new_chat_id
            if self.notifier:
                self.notifier.chat_id = new_chat_id
            
            print(f"💬 Chat ID actualizado: {old_chat_id} → {new_chat_id}")
            self.log_event("CONFIG", f"Chat ID actualizado: {old_chat_id} → {new_chat_id}")
            return True
        else:
            self.log_event("ERROR", "Error actualizando Chat ID en config.py")
            return False
    
    def get_stats(self):
        """Obtiene estadísticas actuales del sistema"""
        uptime = time.time() - self.stats['uptime_start']
        return {
            **self.stats,
            'uptime': uptime,
            'detection_active': self.is_detection_active,
            'current_chat_id': self.current_chat_id,
            'camera_active': self.cap is not None and self.cap.isOpened() if self.cap else False
        }
    
    def log_event(self, level, message):
        """Registra un evento en el sistema de logs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        
        with self.logs_lock:
            self.logs.insert(0, log_entry)  # Agregar al inicio
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[:self.max_logs]  # Mantener límite
        
        print(f"📋 [{timestamp}] {level}: {message}")
    
    def get_logs(self):
        """Obtiene los logs actuales"""
        with self.logs_lock:
            return self.logs.copy()
    
    def stop(self):
        """Detiene el sistema de forma segura"""
        print("🛑 Deteniendo WebHelmetSystem...")
        self.running = False
        
        if self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=5)
        
        if self.cap:
            self.cap.release()
        
        self.log_event("SYSTEM", "Sistema detenido")

# Instancia global del sistema
helmet_system = None

def get_helmet_system():
    """Obtiene o crea la instancia del sistema"""
    global helmet_system
    if helmet_system is None:
        helmet_system = WebHelmetSystem()
    return helmet_system

# ===== RUTAS DE LA APLICACIÓN =====

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html', config=config)

@app.route('/api/frame')
def api_frame():
    """API para obtener el frame actual"""
    try:
        system = get_helmet_system()
        frame_data, violation = system.get_current_frame()
        
        if frame_data:
            return jsonify({
                'success': True,
                'frame': frame_data,
                'violation': violation,
                'detection_active': system.is_detection_active,
                'stats': system.get_stats()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No hay frame disponible'
            }), 503
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/logs')
def api_logs():
    """API para obtener los logs del sistema"""
    try:
        system = get_helmet_system()
        return jsonify(system.get_logs())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def api_stats():
    """API para obtener estadísticas del sistema"""
    try:
        system = get_helmet_system()
        return jsonify(system.get_stats())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/toggle_detection', methods=['POST'])
def api_toggle_detection():
    """API para activar/desactivar la detección"""
    try:
        system = get_helmet_system()
        status = system.toggle_detection()
        return jsonify({
            'success': True,
            'detection_active': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/update_chat_id', methods=['POST'])
def api_update_chat_id():
    """API para actualizar el Chat ID"""
    try:
        data = request.get_json()
        
        if not data or 'chat_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Chat ID no proporcionado'
            }), 400
        
        new_chat_id = str(data['chat_id']).strip()
        
        if not new_chat_id:
            return jsonify({
                'success': False,
                'error': 'Chat ID no puede estar vacío'
            }), 400
        
        system = get_helmet_system()
        
        if system.update_chat_id(new_chat_id):
            return jsonify({
                'success': True,
                'chat_id': new_chat_id,
                'message': 'Chat ID actualizado correctamente en config.py'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error actualizando config.py'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test_notification', methods=['POST'])
def api_test_notification():
    """API para enviar notificación de prueba"""
    try:
        system = get_helmet_system()
        
        # Obtener frame actual
        frame_data, _ = system.get_current_frame()
        
        if not frame_data:
            return jsonify({
                'success': False,
                'error': 'No hay frame disponible para la prueba'
            }), 503
        
        # Decodificar frame
        import base64
        frame_bytes = base64.b64decode(frame_data)
        import numpy as np
        frame_array = cv2.imdecode(
            np.frombuffer(frame_bytes, np.uint8), 
            cv2.IMREAD_COLOR
        )
        
        if system.send_notification(frame_array):
            return jsonify({
                'success': True,
                'message': 'Notificación de prueba enviada correctamente'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error enviando notificación'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===== MANEJO DE ERRORES =====

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Error interno del servidor'}), 500
@app.route('/api/video_sources')
def api_video_sources():
    """API para obtener fuentes de video disponibles"""
    try:
        sources = config.get_available_sources()
        return jsonify(sources)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/current_source')
def api_current_source():
    """API para obtener la fuente actual"""
    try:
        system = get_helmet_system()
        current_source = config.get_current_source()
        
        # Determinar valor actual para el selector
        if config.USE_WEBCAM:
            current_value = f"webcam_{config.WEBCAM_ID}"
        else:
            current_value = f"video_{config.CURRENT_VIDEO_INDEX}"
        
        return jsonify({
            'current_source': current_source,
            'current_value': current_value,
            'use_webcam': config.USE_WEBCAM,
            'webcam_id': config.WEBCAM_ID,
            'video_path': config.VIDEO_PATH
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/change_video_source', methods=['POST'])
def api_change_video_source():
    """API para cambiar la fuente de video"""
    try:
        data = request.get_json()
        
        if not data or 'source' not in data:
            return jsonify({
                'success': False,
                'error': 'Fuente no especificada'
            }), 400
        
        source_value = data['source']
        
        # Parsear el valor de la fuente (formato: "webcam_0" o "video_1")
        if source_value.startswith('webcam_'):
            camera_id = int(source_value.split('_')[1])
            success = change_to_webcam(camera_id)
            current_source = f"Cámara {camera_id}"
        elif source_value.startswith('video_'):
            video_index = int(source_value.split('_')[1])
            success = change_to_video(video_index)
            current_source = f"Video: {config.AVAILABLE_VIDEOS[video_index]}"
        else:
            return jsonify({
                'success': False,
                'error': 'Formato de fuente inválido'
            }), 400
        
        if success:
            return jsonify({
                'success': True,
                'current_source': current_source,
                'message': f'Cambiado a: {current_source}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error cambiando fuente de video'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test_video_source', methods=['POST'])
def api_test_video_source():
    """API para probar una fuente de video"""
    try:
        data = request.get_json()
        source_value = data.get('source', '')
        
        # Probar la fuente sin cambiarla permanentemente
        if source_value.startswith('webcam_'):
            camera_id = int(source_value.split('_')[1])
            success = test_camera(camera_id)
            message = f"Cámara {camera_id} {'disponible' if success else 'no disponible'}"
        elif source_value.startswith('video_'):
            video_index = int(source_value.split('_')[1])
            success = test_video_file(video_index)
            video_name = config.AVAILABLE_VIDEOS[video_index]
            message = f"Video {video_name} {'disponible' if success else 'no encontrado'}"
        else:
            return jsonify({
                'success': False,
                'error': 'Formato de fuente inválido'
            }), 400
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# AGREGAR ESTAS FUNCIONES HELPER AL FINAL DE app.py:

def change_to_webcam(camera_id):
    """Cambia a una cámara web específica"""
    try:
        global helmet_system
        
        # Actualizar configuración
        config.USE_WEBCAM = True
        config.WEBCAM_ID = camera_id
        config.VIDEO_SOURCE_TYPE = 'webcam'
        config.CURRENT_CAMERA_ID = camera_id
        
        # Reiniciar sistema de cámara
        if helmet_system:
            helmet_system.stop()
            helmet_system = None
        
        # Crear nuevo sistema
        system = get_helmet_system()
        system.log_event("CONFIG", f"Cambiado a cámara {camera_id}")
        
        return True
        
    except Exception as e:
        print(f"Error cambiando a cámara {camera_id}: {e}")
        return False

def change_to_video(video_index):
    """Cambia a un video específico"""
    try:
        global helmet_system
        
        if video_index >= len(config.AVAILABLE_VIDEOS):
            return False
        
        # Actualizar configuración
        config.USE_WEBCAM = False
        config.VIDEO_PATH = config.AVAILABLE_VIDEOS[video_index]
        config.VIDEO_SOURCE_TYPE = 'video'
        config.CURRENT_VIDEO_INDEX = video_index
        
        # Reiniciar sistema de cámara
        if helmet_system:
            helmet_system.stop()
            helmet_system = None
        
        # Crear nuevo sistema
        system = get_helmet_system()
        system.log_event("CONFIG", f"Cambiado a video: {config.VIDEO_PATH}")
        
        return True
        
    except Exception as e:
        print(f"Error cambiando a video {video_index}: {e}")
        return False

def test_camera(camera_id):
    """Prueba si una cámara está disponible"""
    try:
        import cv2
        cap = cv2.VideoCapture(camera_id)
        
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            return ret and frame is not None
        
        return False
        
    except Exception as e:
        print(f"Error probando cámara {camera_id}: {e}")
        return False

def test_video_file(video_index):
    """Prueba si un archivo de video existe y es válido"""
    try:
        if video_index >= len(config.AVAILABLE_VIDEOS):
            return False
        
        video_path = config.AVAILABLE_VIDEOS[video_index]
        
        # Verificar que el archivo existe
        import os
        if not os.path.exists(video_path):
            return False
        
        # Verificar que se puede abrir
        import cv2
        cap = cv2.VideoCapture(video_path)
        
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            return ret and frame is not None
        
        return False
        
    except Exception as e:
        print(f"Error probando video {video_index}: {e}")
        return False
# ===== PUNTO DE ENTRADA =====
# REEMPLAZA LA PARTE FINAL DE app.py (líneas finales) CON ESTO:

if __name__ == '__main__':
    import numpy as np
    import os
    
    try:
        print("🚀 INICIANDO SISTEMA WEB DE DETECCIÓN DE CASCOS")
        print("=" * 60)
        print("📹 Cámara: Se activará automáticamente")
        print("🔍 Detección: DESACTIVADA (activar desde interfaz web)")
        print("💾 Configuración: Se guardará automáticamente en config.py")
        
        # Obtener puerto para producción (Railway, Heroku, etc.)
        port = int(os.environ.get('PORT', 5000))
        host = os.environ.get('HOST', '0.0.0.0')
        
        print(f"🌐 Servidor: http://{host}:{port}")
        print("=" * 60)
        
        # Inicializar sistema
        system = get_helmet_system()
        
        # Configurar Flask para producción
        app.run(
            debug=False,
            host=host,
            port=port,
            threaded=True,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servidor...")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if helmet_system:
            helmet_system.stop()
        print("👋 Sistema detenido correctamente")