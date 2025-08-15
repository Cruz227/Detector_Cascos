# notifier.py - Versión actualizada para aplicación web
import cv2
import telegram
import asyncio
import threading
from datetime import datetime

class TelegramNotifier:
    """
    Clase para gestionar las notificaciones de alerta a través de un bot de Telegram.
    Versión actualizada para aplicación web.
    """
    def __init__(self, token, chat_id):
        """
        Inicializa el bot de Telegram si se proporcionan credenciales válidas.
        """
        self.token = token
        self.chat_id = chat_id
        self.bot = None
        self.last_error = None
        
        if token and chat_id:
            try:
                self.bot = telegram.Bot(token=token)
                print("INFO: Notificador de Telegram inicializado correctamente.")
            except Exception as e:
                self.last_error = str(e)
                print(f"WARN: No se pudo inicializar el bot: {e}. Notificaciones desactivadas.")
                self.bot = None
        else:
            print("INFO: Credenciales de Telegram no proporcionadas. Notificaciones desactivadas.")

    def send_alert(self, image_with_violation):
        """
        Envía la alerta de forma no bloqueante usando threading.
        """
        if not self.bot:
            print("WARN: Bot de Telegram no disponible")
            return False
        
        def send_async():
            try:
                # Crear nuevo loop de eventos para este hilo
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Ejecutar el envío asíncrono
                loop.run_until_complete(self._async_send_alert(image_with_violation))
                loop.close()
                
                print("INFO: Alerta enviada a Telegram con éxito.")
                return True
                
            except Exception as e:
                self.last_error = str(e)
                print(f"ERROR: Fallo al enviar la notificación: {e}")
                return False
        
        # Ejecutar en hilo separado para no bloquear Flask
        thread = threading.Thread(target=send_async, daemon=True)
        thread.start()
        
        return True  # Retorna True inmediatamente (envío asíncrono)

    async def _async_send_alert(self, image_with_violation):
        """
        Función asíncrona que realmente envía la foto.
        """
        caption = f"🚨 ALERTA DE SEGURIDAD 🚨\n\n" \
                 f"Se ha detectado una persona sin casco de seguridad.\n" \
                 f"Fecha y hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n" \
                 f"Sistema de monitoreo automático."
        
        _, buffer = cv2.imencode('.jpg', image_with_violation)
        
        await self.bot.send_photo(
            chat_id=self.chat_id,
            photo=buffer.tobytes(),
            caption=caption
        )