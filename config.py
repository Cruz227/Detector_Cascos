# config.py - VERSIÓN MEJORADA CON MÚLTIPLES FUENTES

import os

# --- CONFIGURACIÓN DE LA FUENTE DE VIDEO ---
# Opciones disponibles: 'webcam', 'video'
VIDEO_SOURCE_TYPE = 'video'  # Por defecto usa video de prueba

# Configuración de cámaras web
AVAILABLE_CAMERAS = [0, 1, 2]  # IDs de cámaras disponibles
CURRENT_CAMERA_ID = 0          # Cámara activa por defecto

# Configuración de videos de prueba
AVAILABLE_VIDEOS = [
    "video_prueba2.mp4",
    "video_prueba2.mp4"  # Puedes agregar más videos aquí
]
CURRENT_VIDEO_INDEX = 0        # Video activo por defecto

# Variables dinámicas (se actualizan desde la web)
USE_WEBCAM = False
WEBCAM_ID = CURRENT_CAMERA_ID
VIDEO_PATH = AVAILABLE_VIDEOS[CURRENT_VIDEO_INDEX]

# --- CONFIGURACIÓN DEL MODELO ---
MODEL_PATH = "best.pt"
# Escribe el nombre exacto de la clase que representa a una persona SIN casco
TARGET_CLASS_NAME = 'head'

# --- CONFIGURACIÓN DE TELEGRAM (SEGURA) ---
# Usa variables de entorno en producción, valores por defecto en desarrollo
BOT_TOKEN = os.environ.get('BOT_TOKEN', "8340677870:AAHd8P1VYF3-z730UeiwpvAe9cwVYmxfKng")
CHAT_ID = os.environ.get('CHAT_ID', " -1002703976307")

# Tiempo de espera entre notificaciones
NOTIFICATION_COOLDOWN_SECONDS = 30

# --- CONFIGURACIÓN WEB ---
WEB_VIDEO_RESIZE = True
WEB_VIDEO_WIDTH = 640
WEB_VIDEO_HEIGHT = 480

# --- FUNCIONES HELPER ---
def get_current_source():
    """Retorna la fuente actual de video"""
    if USE_WEBCAM:
        return f"Cámara {WEBCAM_ID}"
    else:
        return f"Video: {VIDEO_PATH}"

def get_available_sources():
    """Retorna todas las fuentes disponibles"""
    sources = []
    
    # Agregar cámaras
    for cam_id in AVAILABLE_CAMERAS:
        sources.append({
            'type': 'webcam',
            'id': cam_id,
            'name': f'Cámara {cam_id}',
            'value': f'webcam_{cam_id}'
        })
    
    # Agregar videos
    for i, video in enumerate(AVAILABLE_VIDEOS):
        sources.append({
            'type': 'video',
            'id': i,
            'name': f'Video: {video}',
            'value': f'video_{i}'
        })
    
    return sources