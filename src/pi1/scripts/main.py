# main.py - Simulación de detección de materiales en una planta de reciclaje
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

# main.py - Script principal para Raspberry Pi 1
import time
import json
import logging
import yaml
import os
import random  # Importar random
import paho.mqtt.client as mqtt
from utils.network_manager import NetworkManager
from utils.real_time_config import RealTimeConfigManager
from utils.config_manager import ConfigManager
from utils.mqtt_client import create_mqtt_client, subscribe_to_topic

# Función para manejar mensajes recibidos desde material/entrada
def on_message(client, userdata, msg):
    logging.info(f"[MQTT] Mensaje recibido en {msg.topic}: {msg.payload.decode()}")

    try:
        # Decodificar mensaje
        payload = json.loads(msg.payload.decode())
        material = payload.get("material", "")
        timestamp = payload.get("timestamp", "")

        logging.info(f"[MAIN] Material detectado: {material} a las {timestamp}")

        # Solo procesar materiales PET o HDPE
        if material in ["PET", "HDPE"]:
            duration = round(random.uniform(1, 5), 2)  # Tiempo aleatorio entre 1 y 5 segundos
            action_message = {"tipo": material, "tiempo": duration}

            # Publicar en valvula/accion
            client.publish("valvula/accion", json.dumps(action_message))
            logging.info(f"[MAIN] Publicado en 'valvula/accion': {action_message}")
        else:
            logging.info(f"[MAIN] Material '{material}' no relevante para activación de relés.")

    except Exception as e:
        logging.error(f"[MAIN] Error procesando mensaje: {e}")

def on_message_received(client, userdata, msg):
    """
    Callback para procesar mensajes recibidos.
    """
    try:
        payload = json.loads(msg.payload.decode())
        detection_id = payload.get("id", "N/A")
        material = payload.get("material", "Unknown")

        logging.info(f"[MAIN] Mensaje recibido | ID: {detection_id} | Material: {material}")

        if material in ["PET", "HDPE"]:
            action_time = round(random.uniform(1, 5), 2)
            action_payload = {"id": detection_id, "tipo": material, "tiempo": action_time}

            # Publicar mensaje para activar válvula
            publish_message(client, "valvula/accion", action_payload)
            logging.info(f"[MAIN] Acción enviada | ID: {detection_id} | Tipo: {material} | Tiempo: {action_time}s")
        else:
            logging.info(f"[MAIN] Material '{material}' ignorado | ID: {detection_id}")

    except Exception as e:
        logging.error(f"[MAIN] Error procesando mensaje: {e}")


# Función principal
def main():
    try:
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # Configuración
        logging.info("=" * 70)
        logging.info("[MAIN] Iniciando sistema de detección de materiales en Raspberry Pi 1")
        logging.info("=" * 70)

        # Cargar configuración
        config_path = "/home/raspberry-1/capstonepupr/src/pi1/config/config.yaml"
        config_manager = RealTimeConfigManager(config_path)
        config_manager.start_monitoring()
        config = config_manager.get_config()

        # Configuración de red
        logging.info("[MAIN] Iniciando monitoreo de red...")
        network_manager = NetworkManager(config)
        network_manager.start_monitoring()

        # Configuración MQTT
        mqtt_config = config["mqtt"]
        client = create_mqtt_client(
            client_id=mqtt_config["client_id"],
            broker_addresses=mqtt_config["broker_addresses"],
            port=mqtt_config["port"],
            keepalive=mqtt_config["keepalive"]
        )

        # Suscribirse al tópico 'material/entrada'
        topic_entry = mqtt_config["topics"]["entry"]
        logging.info(f"[MAIN] Suscribiéndose al tópico '{topic_entry}'...")
        client.subscribe(topic_entry)
        client.message_callback_add(topic_entry, on_message)

        logging.info("[MAIN] Esperando señales desde Raspberry Pi 3...")
        client.loop_forever()

    except KeyboardInterrupt:
        logging.info("[MAIN] Apagando Monitoreo del Network...")
        network_manager.stop_monitoring()
        logging.info("[MAIN] Sistema apagado correctamente.")
    except Exception as e:
        logging.error(f"[MAIN] Error crítico en la ejecución: {e}")
    finally:
        logging.info("[MAIN] Finalizando ejecución del script.")
        mqtt_client.disconnect()
        logging.info("[MAIN] Cliente MQTT desconectado.")


if __name__ == "__main__":
    main()

