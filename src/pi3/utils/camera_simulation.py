# camera_simulation.py - Simula la detección de materiales mediante una cámara
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import time
import random
import json
import logging
from datetime import datetime
from utils.mqtt_handler import MQTTHandler
from waste_type import generate_waste_data

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

    while True:
        try:
            # Simular detección aleatoria de materiales
            material_detected = random.choice(["PET", "HDPE", "PVC", "LDPE", "PP", "PS", "Other"])
            timestamp = time.time()

            payload = {
                "status": "material_detected",
                "material": material_detected,
                "timestamp": timestamp
            }

            # Publicar en el tópico MQTT usando la instancia de MQTTHandler
            mqtt_handler.publish(topic, payload)

            logging.info(f"[CAMERA] Material detectado: {material_detected}. Enviado al tópico '{topic}'.")

            # Simular el tiempo de detección
            wait_time = random.uniform(*detection_range)
            logging.info(f"[CAMERA] Esperando {wait_time:.2f} segundos antes de la próxima detección.")
            time.sleep(wait_time)

        except KeyboardInterrupt:
            logging.info("[CAMERA] Simulación de cámara detenida por el usuario.")
            break
        except Exception as e:
            logging.error(f"[CAMERA] Error durante la simulación de detección: {e}")
            break