# config.py - ACTUALIZA CON ESTA VERSIÓN SEGURA

import os

# --- CONFIGURACIÓN DE LA FUENTE DE VIDEO ---
# True = Usar cámara web | False = Usar archivo de video
USE_WEBCAM = False
WEBCAM_ID = 0
VIDEO_PATH = "video_prueba2.mp4"

# --- CONFIGURACIÓN DEL MODELO ---
MODEL_PATH = "best.pt"
# Escribe el nombre exacto de la clase que representa a una persona SIN casco
# esta clase podría ser 'cabeza', 'person', 'no-helmet', etc.
TARGET_CLASS_NAME = 'head'

# --- CONFIGURACIÓN DE TELEGRAM (SEGURA) ---
# Usa variables de entorno en producción, valores por defecto en desarrollo
BOT_TOKEN = os.environ.get('BOT_TOKEN', "8340677870:AAHd8P1VYF3-z730UeiwpvAe9cwVYmxfKng")
CHAT_ID = os.environ.get('CHAT_ID', " -1002703976307")

# Tiempo de espera (en segundos) entre notificaciones para evitar spam
NOTIFICATION_COOLDOWN_SECONDS = 30

# --- CONFIGURACIÓN ADICIONAL PARA WEB ---
# Configuración de video para web (opcional)
WEB_VIDEO_RESIZE = True  # Redimensionar video para mejor rendimiento web
WEB_VIDEO_WIDTH = 640    # Ancho del video para web
WEB_VIDEO_HEIGHT = 480   # Alto del video para web