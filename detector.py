# detector.py
from ultralytics import YOLO

class HelmetDetector:
    """
    Clase para manejar el modelo YOLO de detección de objetos.
    """
    def __init__(self, model_path):
        """
        Inicializa y carga el modelo YOLO.
        """
        try:
            self.model = YOLO(model_path)
            self.class_names = self.model.names
            print(f"INFO: Modelo '{model_path}' cargado. Clases: {self.class_names}")
        except Exception as e:
            print(f"ERROR: No se pudo cargar el modelo YOLO desde '{model_path}': {e}")
            raise  # Detiene la ejecución si el modelo no carga

    def detect_on_frame(self, frame):
        """
        Realiza la detección de objetos en un solo frame.
        """
        return self.model(frame)

    def find_violation(self, results, target_class):
        """
        Revisa los resultados de la detección para encontrar la clase objetivo (violación).
        """
        for r in results:
            for box in r.boxes:
                class_name = self.class_names[int(box.cls[0])]
                if class_name == target_class:
                    return True
        return False

    def draw_detections(self, results):
        """
        Dibuja los cuadros de detección en el frame.
        """
        return results[0].plot()