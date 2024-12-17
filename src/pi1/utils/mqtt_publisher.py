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
    detection_interval = simulation_config["detection_interval"]
    valve_duration_range = simulation_config["valve_duration"]

    while True:
        try:
            # Generar mensaje aleatorio
            material_type = random.choice(["PET", "HDPE"])
            duration = random.randint(*valve_duration_range)
            message = {"tipo": material_type, "tiempo": duration}

            # Publicar mensaje en el tópico
            client.publish(topic_action, json.dumps(message))
            logging.info(f"[PUBLISHER] Mensaje publicado en {topic_action}: {message}")

            # Espera aleatoria entre detecciones
            wait_time = random.randint(*detection_interval)
            logging.info(f"[PUBLISHER] Esperando {wait_time} segundos antes de la próxima detección.")
            time.sleep(wait_time)

        except Exception as e:
            logging.error(f"[PUBLISHER] Error durante la simulación: {e}")
            break