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
from utils.mqtt_handler import MQTTHandler
from utils.waste_type import WasteTypeDetector

# Configuración del logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def simulate_camera_detection(mqtt_handler, topic, detection_range):
    """
    Simula la detección de materiales usando una cámara y envía los resultados al tópico MQTT.

    :param mqtt_handler: Instancia del manejador MQTT.
    :param topic: Tópico MQTT donde se enviarán los mensajes.
    :param detection_range: Rango de tiempo aleatorio entre detecciones (en segundos).
    """
    logging.info("[CAMERA] Iniciando simulación de detección de materiales...")
    try:
        while True:
                # Simular detección de materiales usando waste_type
                waste_data = simulate_waste_detection()

                # Extraer un material aleatorio de los detectados
                detected_materials = waste_data.get("detected_items", [])
                if detected_materials:
                    material = detected_materials[0]["Name"]  # Tomar el primer material detectado
                else:
                    material = "Unknown"

                # Crear mensaje de detección
                detection_message = {
                    "id": str(uuid.uuid4()),  # ID único
                    "status": "material_detected",
                    "material": material,  # Material detectado
                    "timestamp": time.time()
                }

                # Publicar en el tópico MQTT
                mqtt_handler.publish(topic, detection_message)
                logging.info(f"[CAMERA] Material detectado: {material}. Enviado al tópico '{topic}'.")

                # Simular delay aleatorio
                wait_time = random.uniform(*delay_range)
                logging.info(f"[CAMERA] Esperando {wait_time:.2f} segundos antes de la próxima detección.")
                time.sleep(wait_time)

    except Exception as e:
        logging.error(f"[CAMERA] Error durante la simulación de detección: {e}")
        raise