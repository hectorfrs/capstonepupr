# camera_simulation.py - Simula la detección de materiales mediante una cámara
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import time
import random
import json
import logging
from datetime import datetime
from utils.mqtt_handler import publish_message
from waste_type import generate_waste_data

# Configuración del logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def simulate_camera_detection(client, topic_entry, detection_interval):
    """
    Simula el uso de una cámara para detectar materiales y publica los resultados en MQTT.

    Args:
        client: Cliente MQTT.
        topic_entry (str): Tópico MQTT donde se publica la entrada del material.
        detection_interval (list): Intervalo mínimo y máximo en segundos entre detecciones.
    """
    logging.info("[CAMERA] Iniciando simulación de detección de materiales con la cámara...")

    try:
        while True:
            # Generar datos simulados de detección de material
            detected_material = generate_waste_data()

            # Filtrar elementos detectables (solo plásticos PET o HDPE)
            plastic_items = [
                item for item in detected_material["detected_items"]
                if item["Name"] in ["PET", "HDPE"]
            ]

            # Simular detección de la cámara
            if plastic_items:
                material = random.choice(plastic_items)
                camera_data = {
                    "material": material["Name"],
                    "confidence": material["Confidence"],
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                # Publicar los datos simulados en el tópico MQTT
                publish_message(client, topic_entry, camera_data)
                logging.info(f"[CAMERA] Material detectado: {camera_data}")

            else:
                logging.info("[CAMERA] No se detectó ningún material relevante.")

            # Esperar un tiempo aleatorio entre detecciones
            wait_time = random.uniform(*detection_interval)
            logging.info(f"[CAMERA] Esperando {wait_time:.2f} segundos antes de la próxima detección.")
            time.sleep(wait_time)

    except KeyboardInterrupt:
        logging.info("[CAMERA] Simulación de cámara finalizada manualmente.")
    except Exception as e:
        logging.error(f"[CAMERA] Error en la simulación de cámara: {e}")