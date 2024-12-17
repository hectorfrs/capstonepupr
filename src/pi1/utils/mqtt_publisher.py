# mqtt_publisher.py - Módulo para publicar mensajes MQTT simulados en un tópico específico.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import random
import time
import json
import logging

def start_publisher(client, topic_action, simulation_config):
    """
    Inicia la publicación de mensajes MQTT simulados para detección de materiales.
    """
    detection_interval = list(map(float, simulation_config["detection_interval"]))
    valve_duration_range = list(map(float, simulation_config["valve_duration"]))

    while True:
        try:
            # Generar mensaje aleatorio
            material_type = random.choice(["PET", "HDPE"])
            duration = random.uniform(*valve_duration_range)  # Generar duración aleatoria en segundos
            message = {"tipo": material_type, "tiempo": round(duration, 2)}  # Redondear a 2 decimales

            # Publicar mensaje en el tópico
            client.publish(topic_action, json.dumps(message))
            logging.info(f"[PUBLISHER] [MQTT] Mensaje publicado en {topic_action}: {message}")

            # Espera aleatoria entre detecciones
            wait_time = random.uniform(*detection_interval)
            logging.info(f"[PUBLISHER] [MQTT] Esperando {wait_time:.2f} segundos antes de la próxima detección.")
            time.sleep(wait_time)  # Espera en segundos (con decimales)

        except Exception as e:
            logging.error(f"[PUBLISHER] [MQTT] Error durante la simulación: {e}")
            break
