# Sistema de Detección de Cascos de Seguridad

## Descripción

Sistema inteligente de monitoreo de seguridad laboral que utiliza visión por computadora para detectar automáticamente cuando las personas no utilizan casco de seguridad en áreas de trabajo. Al detectar una infracción, el sistema envía instantáneamente una notificación y fotografía vía Telegram para una respuesta inmediata.

## Características Principales

- **Detección en Tiempo Real**: Análisis continuo de video utilizando modelo YOLO entrenado específicamente para detectar cascos de seguridad
- **Notificaciones Automáticas**: Envío inmediato de alertas vía Telegram cuando se detecta una infracción
- **Interfaz Web**: Panel de control moderno y responsivo para monitoreo y configuración
- **Fuentes de Video Múltiples**: Soporte para cámaras web y archivos de video de prueba
- **Configuración Dinámica**: Cambio de parámetros desde la interfaz web sin reiniciar el sistema

## Tecnologías Utilizadas

### Backend
- **Python 3.9+**: Lenguaje principal
- **Flask**: Framework web para API REST
- **OpenCV**: Procesamiento de video e imágenes
- **Ultralytics YOLO**: Modelo de detección de objetos
- **python-telegram-bot**: Integración con Telegram

### Frontend
- **HTML5**: Estructura semántica
- **CSS3**: Diseño moderno con glassmorphism
- **JavaScript ES6**: Lógica interactiva y comunicación con API

### Inteligencia Artificial
- **Modelo YOLO Personalizado**: Red neuronal entrenada para detectar personas con y sin casco
- **Clases de Detección**: `head` (persona sin casco), `helmet` (persona con casco)

## Estructura del Proyecto

```
TALENTOTECH_PROYECTOFINAL/
├── app.py                  # Servidor Flask y API REST
├── config.py               # Configuración del sistema
├── detector.py             # Lógica de detección YOLO
├── notifier.py             # Sistema de notificaciones Telegram
├── main.py                 # Aplicación de consola original
├── best.pt                 # Modelo YOLO entrenado
├── requirements.txt        # Dependencias Python
├── .gitignore             # Archivos excluidos de Git
├── templates/
│   └── index.html         # Interfaz web principal
├── static/
│   ├── css/
│   │   └── style.css      # Estilos modernos con glassmorphism
│   ├── js/
│   │   └── helmet-app.js  # Lógica JavaScript modular
│   └── img/
│       └── favicon.ico    # Icono de la aplicación
├── video_prueba.mp4       # Video de prueba 1
├── video_prueba2.mp4      # Video de prueba 2
└── __pycache__/           # Cache de Python (auto-generado)
```

## Instalación y Configuración

### Prerrequisitos
- Python 3.9 o superior
- Cámara web (opcional)
- Bot de Telegram configurado

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/usuario/Detector_Cascos.git
   cd Detector_Cascos
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar Telegram**
   - Crear bot con @BotFather
   - Obtener Bot Token
   - Obtener Chat ID usando @userinfobot
   - Actualizar `config.py` con las credenciales

### Configuración de Telegram

1. **Crear Bot**:
   - Enviar `/newbot` a @BotFather en Telegram
   - Seguir instrucciones y obtener el token

2. **Obtener Chat ID**:
   - Enviar mensaje a @userinfobot
   - Copiar el ID numérico

3. **Actualizar configuración**:
   ```python
   # En config.py
   BOT_TOKEN = "tu_bot_token_aqui"
   CHAT_ID = "tu_chat_id_aqui"
   ```

## Uso del Sistema

### Modo Consola
```bash
python main.py
```

### Modo Web (Recomendado)
```bash
python app.py
```
Abrir navegador en: `http://localhost:5000`

## Funcionalidades de la Interfaz Web

### Panel Principal
- **Video en Tiempo Real**: Visualización del stream con detecciones marcadas
- **Estados Visuales**: Indicadores de cámara activa y estado de detección
- **Controles de Detección**: Activar/desactivar monitoreo de infracciones

### Configuración
- **Chat ID de Telegram**: Modificación dinámica del destinatario de alertas
- **Prueba de Notificaciones**: Envío de alertas de prueba
- **Fuente de Video**: Selección entre cámara web y videos de prueba

### Monitoreo
- **Estadísticas en Tiempo Real**: Contadores de detecciones, infracciones y notificaciones
- **Registro de Actividad**: Logs detallados de eventos del sistema
- **Tiempo de Actividad**: Monitoreo del tiempo de funcionamiento

## Configuración Avanzada

### Parámetros de Detección
```python
# config.py
TARGET_CLASS_NAME = 'head'  # Clase que representa infracción
NOTIFICATION_COOLDOWN_SECONDS = 30  # Tiempo entre alertas
```

### Fuentes de Video
```python
# Cámara web
USE_WEBCAM = True
WEBCAM_ID = 0  # ID de la cámara (0, 1, 2...)

# Archivo de video
USE_WEBCAM = False
VIDEO_PATH = "video_prueba2.mp4"
```

### Optimización de Rendimiento
```python
WEB_VIDEO_RESIZE = True
WEB_VIDEO_WIDTH = 640
WEB_VIDEO_HEIGHT = 480
```

## API REST

### Endpoints Principales
- `GET /api/frame` - Obtener frame actual con detecciones
- `GET /api/stats` - Estadísticas del sistema
- `GET /api/logs` - Registro de eventos
- `POST /api/toggle_detection` - Activar/desactivar detección
- `POST /api/update_chat_id` - Actualizar Chat ID
- `POST /api/test_notification` - Enviar notificación de prueba

### Ejemplo de Respuesta
```json
{
  "success": true,
  "frame": "base64_encoded_image",
  "violation": false,
  "detection_active": true,
  "stats": {
    "total_detections": 1250,
    "violations_detected": 15,
    "notifications_sent": 12,
    "uptime": 3600
  }
}
```

## Modelo de IA

### Arquitectura
- **Base**: YOLOv8 (You Only Look Once)
- **Entrenamiento**: Dataset personalizado de personas con/sin casco
- **Precisión**: Optimizado para entornos industriales
- **Velocidad**: ~30 FPS en hardware estándar

### Clases de Detección
- `head`: Persona sin casco (INFRACCIÓN)
- `helmet`: Persona con casco (CORRECTO)

### Rendimiento
- **Precisión**: >90% en condiciones controladas
- **Recall**: >85% para detección de infracciones
- **Latencia**: <100ms por frame

## Despliegue en Producción

### Plataformas Recomendadas
- **Render.com**: Fácil despliegue con GitHub
- **Railway.app**: Deploy automático
- **PythonAnywhere**: Especializado en Python

### Variables de Entorno
```bash
BOT_TOKEN=tu_bot_token
CHAT_ID=tu_chat_id
PORT=5000
```

## Solución de Problemas

### Problemas Comunes

1. **Cámara no detectada**
   - Verificar permisos de cámara
   - Probar diferentes IDs (0, 1, 2)
   - Cerrar otras aplicaciones que usen la cámara

2. **Notificaciones no llegan**
   - Verificar Bot Token y Chat ID
   - Comprobar conexión a internet
   - Usar función de prueba en la interfaz

3. **Detecciones erróneas**
   - Ajustar iluminación del área
   - Verificar calidad del video
   - Considerar reentrenamiento del modelo

## Changelog

### v2.0.0 - Interfaz Web
- Interfaz web completa con panel de control
- API REST para integración
- Configuración dinámica desde web
- Estadísticas en tiempo real

### v1.0.0 - Versión Consola
- Detección básica por consola
- Notificaciones Telegram
- Soporte para video y cámara web
