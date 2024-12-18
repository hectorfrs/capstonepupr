# camera_simulation.py - Simula la detección de materiales mediante una cámara
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import time
import random
import json
import logging
import uuid
from datetime import datetime
from modules.mqtt_handler import MQTTHandler
from utils.waste_type import WasteTypeDetector

# Configuración del logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def simulate_camera_detection(mqtt_handler, topic, delay_range):
    """
    Simula la detección de materiales y publica mensajes en MQTT usando WasteTypeDetector.
    :param mqtt_handler: Instancia de MQTTHandler para la comunicación MQTT.
    :param topic: Tópico MQTT donde se publicarán los datos de detección.
    :param delay_range: Rango de tiempo (segundos) entre simulaciones de detección.
    """
    detector = WasteTypeDetector()  # Instancia de WasteTypeDetector

    try:
        while True:
            # Generar datos simulados de detección de residuos
            waste_data = detector.generate_waste_data()

            # Extraer un elemento detectado para simular la detección de la cámara
            detected_materials = waste_data.get("detected_items", [])
            if detected_materials:
                detected_item = random.choice(detected_materials)
                material = detected_item["Name"]
                confidence = detected_item["Confidence"]
            else:
                material = "Unknown"
                confidence = 0.0

            # Crear mensaje para MQTT
            detection_message = {
                "id": str(uuid.uuid4()),
                "status": "material_detected",
                "material": material,
                "confidence": confidence,
                "weight": waste_data["total_weight"],  # Peso total de los materiales detectados
                "timestamp": time.time()
            }

            # Publicar el mensaje en MQTT
            mqtt_handler.publish(topic, detection_message)
            logging.info(f"[CAMERA] Material detectado: {material} (Confianza: {confidence}%). Publicado en '{topic}'.")

            # Simular delay aleatorio entre detecciones
            wait_time = random.uniform(*delay_range)
            logging.info(f"[CAMERA] Esperando {wait_time:.2f} segundos antes de la próxima detección.")
            time.sleep(wait_time)

    except KeyboardInterrupt:
        logging.info("[CAMERA] Simulación de cámara detenida por el usuario.")
    except Exception as e:
        logging.error(f"[CAMERA] Error durante la simulación de detección: {e}")
        raise