# main.py
import cv2
import time
import config  # Importamos nuestro archivo de configuración
from detector import HelmetDetector
from notifier import TelegramNotifier

def main():
    # Inicializar los componentes desde nuestros módulos
    detector = HelmetDetector(config.MODEL_PATH)
    notifier = TelegramNotifier(config.BOT_TOKEN, config.CHAT_ID)

    # Configurar la fuente de video
    source = config.WEBCAM_ID if config.USE_WEBCAM else config.VIDEO_PATH
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"ERROR: No se pudo abrir la fuente de video: {source}")
        return

    last_notification_time = 0
    print("INFO: Iniciando la detección en tiempo real. Presiona 'q' para salir.")

    # Bucle principal
    while True:
        ret, frame = cap.read()
        if not ret:
            print("INFO: Fin del stream de video.")
            break

        # 1. Realizar detección
        results = detector.detect_on_frame(frame)
        
        # 2. Comprobar si hay violaciones
        is_violation = detector.find_violation(results, config.TARGET_CLASS_NAME)
        
        # 3. Enviar notificación si es necesario (con cooldown)
        current_time = time.time()
        if is_violation and (current_time - last_notification_time) > config.NOTIFICATION_COOLDOWN_SECONDS:
            annotated_frame = detector.draw_detections(results)
            if notifier.send_alert(annotated_frame):
                last_notification_time = current_time # Actualizar solo si se envió

        # 4. Mostrar el video en pantalla
        display_frame = detector.draw_detections(results)
        cv2.imshow("Detector de Cascos", display_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    # Liberar recursos
    cap.release()
    cv2.destroyAllWindows()
    print("INFO: Aplicación finalizada.")

if __name__ == "__main__":
    main()