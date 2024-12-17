# main.py - Simulación de detección de materiales en una planta de reciclaje
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import time
import json
import logging
from utils.network_manager import NetworkManager
from utils.real_time_config import RealTimeConfigManager
from utils.config_manager import ConfigManager
from utils.mqtt_publisher import start_publisher
from utils.mqtt_client import create_mqtt_client, subscribe_to_topic

# Configurar logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')

def main():
    try:
        # Configuración inicial
        config_path = "/home/raspberry-1/capstonepupr/src/pi1/config/config.yaml"
        
        logging.info("=" * 70)
        logging.info("[MAIN] Iniciando sistema de detección de materiales en Raspberry Pi 1")
        logging.info("=" * 70)

        # Cargar configuración
        logging.info("[MAIN] Cargando configuración...")
        config_manager = RealTimeConfigManager(config_path)
        config_manager.start_monitoring()
        config = config_manager.get_config()

        # Configuración de red
        logging.info("[MAIN] Iniciando monitoreo de red...")
        network_manager = NetworkManager(config)
        network_manager.start_monitoring()

        # Configuración MQTT
        broker_addresses = config["mqtt"]["broker_addresses"]
        port = config["mqtt"]["port"]
        keepalive = config["mqtt"]["keepalive"]
        client_id = config["mqtt"]["client_id"]
        topic_entry = config["mqtt"]["topics"]["entry"]
        topic_action = config["mqtt"]["topics"]["action"]

        # Crear cliente MQTT
        logging.info("[MAIN] Inicializando cliente MQTT...")
        mqtt_client = create_mqtt_client(client_id, broker_addresses, port, keepalive)
        logging.info("[MAIN] Cliente MQTT conectado exitosamente.")

        # Callback para manejar la señal desde Raspberry Pi 3
        def on_material_entry(client, userdata, msg):
            payload = json.loads(msg.payload.decode())
            logging.info(f"[MAIN] Mensaje recibido en '{topic_entry}': {payload}")

            if payload.get("status") == "material_detected":
                weight = payload.get("weight", 0)
                logging.info(f"[MAIN] Material detectado con peso: {weight} g")
                
                # Simular detección de materiales y publicar
                logging.info("[MAIN] Iniciando simulación de detección de materiales...")
                start_publisher(mqtt_client, topic_action, config["simulation"])

        # Suscribirse al tópico 'material/entrada'
        logging.info(f"[MAIN] Suscribiéndose al tópico '{topic_entry}'...")
        subscribe_to_topic(mqtt_client, topic_entry)
        mqtt_client.message_callback_add(topic_entry, on_material_entry)

        # Esperar mensajes
        logging.info("[MAIN] Esperando señales desde Raspberry Pi 3...")
        mqtt_client.loop_forever()

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
